package main

import (
	"io"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		d, _ := io.ReadAll(r.Body)
		defer r.Body.Close()
		io.WriteString(w, "Hello, World!")
		io.WriteString(w, "Got: "+string(d))
	})
	http.ListenAndServe(":8080", nil)
}
