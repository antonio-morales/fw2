package main

import (
	"bytes"
	"flag"
	"fmt"
	"io"
	"math/rand"
	"net"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

type config struct {
	address    string
	iterations int
	timeout    time.Duration
	maxRead    int
	seed       int64
}

type header struct {
	name  string
	value string
}

type requestParts struct {
	method     string
	target     string
	version    string
	headers    []header
	body       []byte
	lineEnding string
}

type attemptResult struct {
	kind       string
	statusLine string
	bytesRead  int
	errText    string
	duration   time.Duration
}

type interestingCase struct {
	signature string
	iteration int
	request   string
	response  string
	result    attemptResult
}

func main() {
	cfg := parseFlags()
	rng := rand.New(rand.NewSource(cfg.seed))
	interesting := make(map[string]interestingCase)

	fmt.Printf("seed=%d\n", cfg.seed)

	for iteration := 1; iteration <= cfg.iterations; iteration++ {
		requestBytes := buildRequest(rng)
		result, responsePreview := sendRequest(cfg, requestBytes)
		signature := makeSignature(result)
		if _, exists := interesting[signature]; exists {
			continue
		}

		entry := interestingCase{
			signature: signature,
			iteration: iteration,
			request:   printable(requestBytes),
			response:  printable(responsePreview),
			result:    result,
		}
		interesting[signature] = entry
		printCase(entry)
	}

	printSummary(interesting)
}

func parseFlags() config {
	cfg := config{}

	flag.StringVar(&cfg.address, "addr", "localhost:80", "TCP address to fuzz")
	flag.IntVar(&cfg.iterations, "iterations", 250, "number of requests to send")
	flag.DurationVar(&cfg.timeout, "timeout", 2*time.Second, "per-request timeout")
	flag.IntVar(&cfg.maxRead, "max-read", 4096, "maximum response bytes to keep")
	flag.Int64Var(&cfg.seed, "seed", time.Now().UnixNano(), "random seed for reproducibility")
	flag.Parse()

	if cfg.iterations <= 0 {
		fmt.Fprintln(os.Stderr, "iterations must be greater than zero")
		os.Exit(2)
	}
	if cfg.maxRead <= 0 {
		fmt.Fprintln(os.Stderr, "max-read must be greater than zero")
		os.Exit(2)
	}

	return cfg
}

func buildRequest(rng *rand.Rand) []byte {
	parts := seedRequestParts(rng)
	mutations := 1 + rng.Intn(4)
	for range mutations {
		mutateParts(rng, &parts)
	}

	rendered := renderRequest(parts)
	rawMutations := rng.Intn(3)
	for range rawMutations {
		rendered = mutateRaw(rng, rendered)
	}

	return rendered
}

func seedRequestParts(rng *rand.Rand) requestParts {
	lineEnding := "\r\n"
	if rng.Intn(6) == 0 {
		lineEnding = "\n"
	}

	body := []byte{}
	method := pick(rng, []string{"GET", "HEAD", "POST", "PUT", "OPTIONS"})
	target := pick(rng, []string{"/", "/health", "/status", "/api", "/index.html", "*"})
	version := pick(rng, []string{"HTTP/1.1", "HTTP/1.0"})
	headers := []header{
		{name: "Host", value: "localhost"},
		{name: "User-Agent", value: "warmup-fuzzer/1.0"},
		{name: "Accept", value: "*/*"},
		{name: "Connection", value: "close"},
	}

	if method == "POST" || method == "PUT" {
		body = randomBytes(rng, 1+rng.Intn(32))
		headers = append(headers, header{name: "Content-Type", value: "application/octet-stream"})
		headers = append(headers, header{name: "Content-Length", value: strconv.Itoa(len(body))})
	}

	return requestParts{
		method:     method,
		target:     target,
		version:    version,
		headers:    headers,
		body:       body,
		lineEnding: lineEnding,
	}
}

func mutateParts(rng *rand.Rand, parts *requestParts) {
	switch rng.Intn(10) {
	case 0:
		parts.method = randomToken(rng, 1+rng.Intn(12))
	case 1:
		parts.target = randomPath(rng)
	case 2:
		parts.version = pick(rng, []string{"HTTP/0.9", "HTTP/1.1", "HTTP/2.0", randomToken(rng, 8)})
	case 3:
		parts.headers = append(parts.headers, header{name: randomHeaderName(rng), value: randomHeaderValue(rng, 16+rng.Intn(128))})
	case 4:
		if len(parts.headers) > 0 {
			index := rng.Intn(len(parts.headers))
			parts.headers[index].value = randomHeaderValue(rng, 1+rng.Intn(512))
		}
	case 5:
		dropHeader(parts, pick(rng, []string{"Host", "Content-Length", "Connection"}))
	case 6:
		parts.headers = append(parts.headers, header{name: "Content-Length", value: strconv.Itoa(rng.Intn(512))})
	case 7:
		parts.body = randomBytes(rng, rng.Intn(256))
	case 8:
		if rng.Intn(2) == 0 {
			parts.lineEnding = "\r\n"
		} else {
			parts.lineEnding = "\n"
		}
	case 9:
		parts.headers = append(parts.headers, header{name: "", value: randomHeaderValue(rng, 8+rng.Intn(64))})
	}
}

func renderRequest(parts requestParts) []byte {
	var builder strings.Builder
	builder.WriteString(parts.method)
	builder.WriteString(" ")
	builder.WriteString(parts.target)
	builder.WriteString(" ")
	builder.WriteString(parts.version)
	builder.WriteString(parts.lineEnding)

	for _, item := range parts.headers {
		if item.name == "" {
			builder.WriteString(item.value)
			builder.WriteString(parts.lineEnding)
			continue
		}
		builder.WriteString(item.name)
		builder.WriteString(": ")
		builder.WriteString(item.value)
		builder.WriteString(parts.lineEnding)
	}

	builder.WriteString(parts.lineEnding)

	packet := []byte(builder.String())
	packet = append(packet, parts.body...)
	return packet
}

func mutateRaw(rng *rand.Rand, packet []byte) []byte {
	if len(packet) == 0 {
		return packet
	}

	switch rng.Intn(5) {
	case 0:
		limit := 1 + rng.Intn(len(packet))
		return append([]byte{}, packet[:limit]...)
	case 1:
		withPrefix := append([]byte{0x00, 0xff}, packet...)
		return withPrefix
	case 2:
		index := rng.Intn(len(packet))
		mutated := append([]byte{}, packet...)
		mutated[index] = byte(rng.Intn(256))
		return mutated
	case 3:
		return append(append([]byte{}, packet...), randomBytes(rng, 1+rng.Intn(32))...)
	case 4:
		return bytes.ReplaceAll(packet, []byte("\r\n"), []byte("\r\r\n"))
	default:
		return packet
	}
}

func sendRequest(cfg config, packet []byte) (attemptResult, []byte) {
	startedAt := time.Now()
	result := attemptResult{}

	conn, err := net.DialTimeout("tcp", cfg.address, cfg.timeout)
	if err != nil {
		result.kind = "dial_error"
		result.errText = err.Error()
		result.duration = time.Since(startedAt)
		return result, nil
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(cfg.timeout))

	if _, err := conn.Write(packet); err != nil {
		result.kind = classifyError(err, "write_error")
		result.errText = err.Error()
		result.duration = time.Since(startedAt)
		return result, nil
	}

	response, readErr := io.ReadAll(io.LimitReader(conn, int64(cfg.maxRead)))
	result.duration = time.Since(startedAt)
	result.bytesRead = len(response)

	if len(response) > 0 {
		result.statusLine = firstLine(response)
		result.kind = "response"
	}

	if readErr == nil {
		if result.kind == "" {
			result.kind = "empty_response"
		}
		return result, response
	}

	if result.kind == "" {
		result.kind = classifyError(readErr, "read_error")
	} else if isTimeout(readErr) {
		result.kind = "response_timeout"
	}
	result.errText = readErr.Error()
	return result, response
}

func makeSignature(result attemptResult) string {
	if result.kind == "response" || result.kind == "response_timeout" {
		return fmt.Sprintf("%s|%s|%s", result.kind, normalizeStatusLine(result.statusLine), sizeBucket(result.bytesRead))
	}
	return fmt.Sprintf("%s|%s", result.kind, normalizeError(result.errText))
}

func printCase(entry interestingCase) {
	fmt.Printf("\n[%s] iteration=%d duration=%s bytes=%d\n", entry.signature, entry.iteration, entry.result.duration.Round(time.Millisecond), entry.result.bytesRead)
	if entry.request != "" {
		fmt.Printf("request:\n%s\n", indent(entry.request))
	}
	if entry.response != "" {
		fmt.Printf("response:\n%s\n", indent(entry.response))
	}
	if entry.result.errText != "" {
		fmt.Printf("error: %s\n", entry.result.errText)
	}
}

func printSummary(interesting map[string]interestingCase) {
	signatures := make([]string, 0, len(interesting))
	for signature := range interesting {
		signatures = append(signatures, signature)
	}
	sort.Strings(signatures)

	fmt.Printf("\nSummary: %d unique outcomes\n", len(signatures))
	for _, signature := range signatures {
		entry := interesting[signature]
		fmt.Printf("- %s (iteration %d)\n", entry.signature, entry.iteration)
	}
}

func dropHeader(parts *requestParts, name string) {
	filtered := parts.headers[:0]
	for _, item := range parts.headers {
		if !strings.EqualFold(item.name, name) {
			filtered = append(filtered, item)
		}
	}
	parts.headers = filtered
}

func firstLine(packet []byte) string {
	scanner := bytes.NewBuffer(packet)
	line, _ := scanner.ReadString('\n')
	return strings.TrimSpace(line)
}

func normalizeStatusLine(statusLine string) string {
	if statusLine == "" {
		return "no-status-line"
	}
	fields := strings.Fields(statusLine)
	if len(fields) >= 2 {
		return fields[0] + " " + fields[1]
	}
	return statusLine
}

func sizeBucket(bytesRead int) string {
	switch {
	case bytesRead == 0:
		return "0"
	case bytesRead < 64:
		return "<64"
	case bytesRead < 512:
		return "<512"
	case bytesRead < 2048:
		return "<2048"
	default:
		return ">=2048"
	}
}

func normalizeError(errText string) string {
	lower := strings.ToLower(errText)
	switch {
	case lower == "":
		return "none"
	case strings.Contains(lower, "connection refused"):
		return "connection-refused"
	case strings.Contains(lower, "reset by peer"):
		return "reset-by-peer"
	case strings.Contains(lower, "broken pipe"):
		return "broken-pipe"
	case strings.Contains(lower, "timeout"):
		return "timeout"
	default:
		return lower
	}
}

func classifyError(err error, fallback string) string {
	switch {
	case isTimeout(err):
		return "timeout"
	case strings.Contains(strings.ToLower(err.Error()), "reset by peer"):
		return "connection_reset"
	default:
		return fallback
	}
}

func isTimeout(err error) bool {
	netErr, ok := err.(net.Error)
	return ok && netErr.Timeout()
}

func randomPath(rng *rand.Rand) string {
	switch rng.Intn(6) {
	case 0:
		return "/" + randomToken(rng, 1+rng.Intn(12))
	case 1:
		return "/" + strings.Repeat("../", 1+rng.Intn(4))
	case 2:
		return "/" + randomToken(rng, 4) + "?" + randomToken(rng, 3) + "=" + randomToken(rng, 12)
	case 3:
		return "/" + strings.Repeat("A", 64+rng.Intn(256))
	case 4:
		return "/%2e%2e/%2f" + randomToken(rng, 6)
	default:
		return "/"
	}
}

func randomHeaderName(rng *rand.Rand) string {
	return pick(rng, []string{
		"X-" + randomToken(rng, 6),
		"Transfer-Encoding",
		"Content-Length",
		"X-Forwarded-For",
		"Expect",
	})
}

func randomHeaderValue(rng *rand.Rand, maxLen int) string {
	length := 1 + rng.Intn(maxLen)
	switch rng.Intn(5) {
	case 0:
		return strings.Repeat("A", length)
	case 1:
		return randomToken(rng, length)
	case 2:
		return "chunked"
	case 3:
		return strconv.Itoa(rng.Intn(1 << 16))
	default:
		return printable(randomBytes(rng, length))
	}
}

func randomBytes(rng *rand.Rand, length int) []byte {
	if length <= 0 {
		return nil
	}

	const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()[]{}-_=+;:',.<>/?\x00\x7f"
	buf := make([]byte, length)
	for index := range buf {
		buf[index] = alphabet[rng.Intn(len(alphabet))]
	}
	return buf
}

func randomToken(rng *rand.Rand, length int) string {
	if length <= 0 {
		return ""
	}

	const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
	buf := make([]byte, length)
	for index := range buf {
		buf[index] = alphabet[rng.Intn(len(alphabet))]
	}
	return string(buf)
}

func printable(packet []byte) string {
	var builder strings.Builder
	for _, item := range packet {
		switch {
		case item == '\r':
			builder.WriteString(`\r`)
		case item == '\n':
			builder.WriteString(`\n`)
			builder.WriteByte('\n')
		case item >= 32 && item <= 126:
			builder.WriteByte(item)
		default:
			builder.WriteString(fmt.Sprintf("\\x%02x", item))
		}
	}
	return strings.TrimSpace(builder.String())
}

func indent(text string) string {
	lines := strings.Split(text, "\n")
	for index, line := range lines {
		lines[index] = "  " + line
	}
	return strings.Join(lines, "\n")
}

func pick(rng *rand.Rand, values []string) string {
	return values[rng.Intn(len(values))]
}
