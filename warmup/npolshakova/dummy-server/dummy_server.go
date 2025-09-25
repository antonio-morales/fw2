package main

import (
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Handle all requests with a simple response
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("Received request:", r.Method, r.URL.Path)
		fmt.Println("Headers:", r.Header)
		fmt.Println("Body:")
		if r.Body != nil {
			defer r.Body.Close()
			body, _ := io.ReadAll(r.Body)
			fmt.Println(string(body))
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Hello, Fuzzer!"))
	})

	// Start the server on localhost:80
	fmt.Println("Starting server on :80")
	err := http.ListenAndServe(":80", nil)
	if err != nil {
		fmt.Println("Error starting server:", err)
	}
}
