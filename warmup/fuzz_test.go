package main

import (
	"context"
	"net/http"
	"strings"
	"testing"
)

func FuzzHTTPServer(f *testing.F) {
	client := http.Client{}
	ctx := context.Background()
	tcs := []string{"{}", "key=value", "/wp-login.php?foo=bar", "", "data", "\x00"}
	for _, tc := range tcs {
		f.Add(tc)
	}
	f.Fuzz(func(t *testing.T, orig string) {
		t.Run("POST", func(t *testing.T) {
			req, err := http.NewRequestWithContext(ctx, "POST", "http://localhost:80", strings.NewReader(orig))
			if err != nil {
				t.Fatal(err)
			}
			_, err = client.Do(req)
			if err != nil {
				t.Fatalf("error making request to server with input %q: %v", orig, err)
			}
		})
		t.Run("GET", func(t *testing.T) {
			req, err := http.NewRequestWithContext(ctx, "GET", "http://localhost:80"+orig, nil)
			if err != nil {
				t.Fatal(err)
			}
			_, err = client.Do(req)
			if err != nil {
				t.Fatalf("error making request to server with input %q: %v", orig, err)
			}
		})
		t.Run("Raw bytes", func(t *testing.T) {
			// TODO: just send crap...
		})
		t.Run("Malformed HTTP data", func(t *testing.T) {
			// Send three sets of headers in a row before a body...
		})
		t.Run("HTTPS data to the HTTP port", func(t *testing.T) {
		})
	})
}
