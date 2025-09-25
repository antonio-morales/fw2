// http_fuzzer.go
package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"

	"crypto/rand"
	"math/big"
	mrand "math/rand"
)

var methods = []string{
	http.MethodGet, http.MethodHead, http.MethodPost,
	http.MethodPut, http.MethodPatch, http.MethodDelete,
	"OPTIONS", "TRACE",
}

var commonHeaders = []string{
	"User-Agent", "Accept", "Accept-Encoding", "Accept-Language",
	"Referer", "X-Forwarded-For", "X-Real-IP", "Content-Type",
	"Cache-Control", "Pragma",
}

func randInt(max int) int {
	n, _ := rand.Int(rand.Reader, big.NewInt(int64(max)))
	return int(n.Int64())
}

func randAlphaNum(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~!$&'()*+,;=:@"
	sb := make([]byte, n)
	// Use math/rand for speed when n large; seed with time.
	for i := range sb {
		sb[i] = letters[mrand.Intn(len(letters))]
	}
	return string(sb)
}

func randSmallString(min, max int) string {
	if max <= min {
		return randAlphaNum(min)
	}
	l := mrand.Intn(max-min+1) + min
	return randAlphaNum(l)
}

func randomPath() string {
	parts := mrand.Intn(4) + 1
	sb := strings.Builder{}
	for i := 0; i < parts; i++ {
		sb.WriteByte('/')
		sb.WriteString(randSmallString(1, 16))
	}
	// maybe add a query
	if mrand.Float32() < 0.4 {
		q := url.Values{}
		pairs := mrand.Intn(5)
		for i := 0; i < pairs; i++ {
			q.Set(randSmallString(1, 8), randSmallString(0, 32))
		}
		sb.WriteString("?" + q.Encode())
	}
	return sb.String()
}

func randomQuery() string {
	parts := mrand.Intn(4) + 1
	sb := strings.Builder{}
	for i := 0; i < parts; i++ {
		sb.WriteString("&")
		sb.WriteString(randAlphaNum(mrand.Intn(10) + 1))
		sb.WriteString("=")
		sb.WriteString(randAlphaNum(mrand.Intn(10) + 1))
	}
	return sb.String()
}

func randomBody() string {
	parts := mrand.Intn(4) + 1
	sb := strings.Builder{}
	for i := 0; i < parts; i++ {
		sb.WriteString(randAlphaNum(mrand.Intn(10) + 1))
	}
	return sb.String()
}

func randomHeaders() http.Header {
	h := http.Header{}
	// random common headers
	for _, k := range commonHeaders {
		if mrand.Float32() < 0.6 {
			// value length and type may vary
			val := randSmallString(0, 40)
			if k == "Content-Type" && mrand.Float32() < 0.5 {
				// common content types
				cts := []string{"application/json", "application/x-www-form-urlencoded", "text/plain", "text/html", "application/octet-stream"}
				val = cts[mrand.Intn(len(cts))]
			}
			h.Set(k, val)
		}
	}
	// add random X- or custom headers occasionally
	if mrand.Float32() < 0.3 {
		for i := 0; i < mrand.Intn(5); i++ {
			h.Set("X-"+randSmallString(1, 8), randSmallString(0, 80))
		}
	}
	return h
}

func main() {
	// Define command-line flags
	targetURL := flag.String("url", "http://localhost:80", "Target URL to fuzz")
	concurrency := flag.Int("concurrency", 10, "Number of concurrent requests")
	flag.Parse()

	// Create a context that we can cancel
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle interrupt signals to gracefully shut down
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-signalChan
		fmt.Println("Received interrupt, shutting down...")
		cancel()
	}()

	// Start fuzzing
	var wg sync.WaitGroup
	for i := 0; i < *concurrency; i++ { // Use concurrency flag
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				default:
					// Create a random request
					method := methods[randInt(len(methods))]
					path := randomPath()
					query := randomQuery()
					body := randomBody()

					// Construct the full URL
					fullURL := fmt.Sprintf("%s%s?%s", *targetURL, path, query)

					// Create a new HTTP request
					req, err := http.NewRequest(method, fullURL, strings.NewReader(body))
					if err != nil {
						fmt.Println("Error creating request:", err)
						continue
					}

					// Add random headers
					req.Header = randomHeaders()

					// Send the request
					resp, err := http.DefaultClient.Do(req)
					if err != nil {
						fmt.Println("Error sending request:", err)
						continue
					}

					// Read and discard the response body
					io.Copy(io.Discard, resp.Body)
					resp.Body.Close()

					// Print the response status
					fmt.Println("Response status:", resp.Status)
				}
			}
		}()
	}

	// Wait for all goroutines to finish
	wg.Wait()
}
