// The Swift Programming Language
// https://docs.swift.org/swift-book
import AsyncHTTPClient

@main
struct fuzzer {
    static func main() async throws {
        let client = HTTPClient()
        var interaction = 0
        while interaction < 100000 {
            interaction += 1
            var request = HTTPClientRequest(url: "http://localhost")
            // Choose a random HTTP method
            let methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            let method = methods.randomElement()!
            request.method = .init(rawValue: method)
            if method == "POST" || method == "PUT" || method == "PATCH" {
                // Add a random body
                let bodySize = Int.random(in: 0...1024)
                let bodyData = (0..<bodySize).map { _ in UInt8.random(in: 0...255) }
                request.body = .bytes(bodyData)
            }
            _ = try await client.execute(request, deadline: .distantFuture)
        }

        try await client.shutdown()
    }
}
