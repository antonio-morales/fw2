package main

import (
	"bytes"
	"fmt"
	"math/rand"
	"net/http"
	"strings"
	"testing"
)

func TestHTTPServer(t *testing.T) {
	for i := range 100 {
		t.Run(fmt.Sprintf("iteration_%d", i), func(t *testing.T) {
			req := generateRandomRequest()

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				t.Logf("Request failed (expected): %v", err)
				return
			}

			defer resp.Body.Close()

			t.Logf("Request succeeded: %s %s", req.Method, req.URL.String())
		})
	}
}

func generateRandomRequest() *http.Request {
	methods := []string{
		"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT",
		generateRandomString(5), "",
	}

	method := methods[rand.Intn(len(methods))]

	host := "localhost:8080"
	path := "/" + generateRandomString(rand.Intn(20))

	if rand.Intn(10) == 0 {
		host = generateRandomString(10)
	}

	url := fmt.Sprintf("http://%s%s", host, path)

	body := generateRandomBody()

	req, err := http.NewRequest(method, url, bytes.NewReader(body))
	if err != nil {
		req, _ = http.NewRequest("GET", "http://localhost:8080/", nil)
	}

	addRandomHeaders(req)

	if rand.Intn(5) == 0 {
		corruptRequest(req)
	}

	return req
}

func generateRandomString(length int) string {
	chars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?"
	var sb strings.Builder
	for range length {
		sb.WriteByte(chars[rand.Intn(len(chars))])
	}
	return sb.String()
}

func generateRandomBody() []byte {
	length := rand.Intn(1000)
	body := make([]byte, length)
	for i := range length {
		body[i] = byte(rand.Intn(256))
	}
	return body
}

func addRandomHeaders(req *http.Request) {
	headers := map[string]string{
		"User-Agent":      generateRandomString(rand.Intn(100)),
		"Content-Type":    generateRandomString(rand.Intn(50)),
		"Authorization":   generateRandomString(rand.Intn(50)),
		"Accept":          generateRandomString(rand.Intn(50)),
		"X-Custom-Header": generateRandomString(rand.Intn(30)),
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	if rand.Intn(3) == 0 {
		for i := 0; i < rand.Intn(5); i++ {
			headerName := generateRandomString(rand.Intn(20))
			req.Header.Set(headerName, generateRandomString(rand.Intn(50)))
		}
	}

	if rand.Intn(10) == 0 {
		longHeader := generateRandomString(10000)
		req.Header.Set("Very-Long-Header", longHeader)
	}
}

func corruptRequest(req *http.Request) {
	if rand.Intn(2) == 0 {
		req.Method = generateRandomString(rand.Intn(20))
	}

	if rand.Intn(2) == 0 {
		queryParams := ""
		for i := 0; i < rand.Intn(5); i++ {
			queryParams += "&" + generateRandomString(5) + "=" + generateRandomString(10)
		}
		req.URL.RawQuery = queryParams
	}
}
