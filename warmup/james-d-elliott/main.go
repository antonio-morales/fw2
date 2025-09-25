package main

import (
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"strings"
	"time"
)

var methods = []string{"GET", "POST", "PUT", "DELETE", "PATCH"}

func randPath(r *rand.Rand) string {
	seg := r.Intn(3) + 1
	parts := make([]string, seg)
	for i := 0; i < seg; i++ {
		parts[i] = randString(r, r.Intn(6)+1)
	}
	return "/" + strings.Join(parts, "/")
}

func randString(r *rand.Rand, l int) string {
	const s = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, l)
	for i := range b {
		b[i] = s[r.Intn(len(s))]
	}
	return string(b)
}

func main() {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	client := &http.Client{Timeout: time.Duration(20) * time.Second}

	var ok, bad int
	for i := 0; i < 1000; i++ {
		method := methods[r.Intn(len(methods))]
		url := "http://localhost:80/" + randPath(r)

		var body io.Reader
		if method != "GET" && r.Float32() < 0.6 {
			body = strings.NewReader(`{"k":"` + randString(r, 6) + `"}`)
		}

		req, err := http.NewRequest(method, url, body)
		if err != nil {
			fmt.Printf("new req err: %v\n", err)
			bad++
			continue
		}
		if body != nil {
			req.Header.Set("Content-Type", "application/json")
		}

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("req err: %v\n", err)
			bad++
			continue
		}
		_, _ = io.Copy(io.Discard, resp.Body)
		resp.Body.Close()

		fmt.Printf("%3d: %s %s -> %d\n", i+1, method, url, resp.StatusCode)
		if resp.StatusCode >= 200 && resp.StatusCode < 400 {
			ok++
		} else {
			bad++
		}
		time.Sleep(50 * time.Millisecond)
	}

	fmt.Printf("ok (2xx/3xx): %d/1000\n", ok)
	fmt.Printf("bad (4xx/5xx/errors): %d/1000\n", bad)
}
