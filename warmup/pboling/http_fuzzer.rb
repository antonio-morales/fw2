require 'net/http'
require 'uri'
require 'openssl'

# Simple HTTP fuzzer for https://localhost:80
TARGET_HOST = 'localhost'
TARGET_PORT = 80
USE_SSL = true
ITERATIONS = 20

HTTP_METHODS = %w[GET POST PUT DELETE PATCH OPTIONS HEAD TRACE CONNECT]
FUZZ_PATHS = [
  '/', '/test', '/fuzz', '/random', '/api', '/v1/resource', '/?q=\x00', '/%00', '/<script>', '/../../etc/passwd'
]
FUZZ_HEADERS = [
  ['X-Fuzz', 'fuzztest'],
  ['User-Agent', 'Fuzzer/1.0'],
  ['X-Exploit', '\x00\x01\x02'],
  ['Referer', 'http://evil.com'],
  ['Cookie', 'session=;'],
  ['Content-Type', 'application/x-www-form-urlencoded'],
  ['Accept', '*/*'],
  ['X-Long-Header', 'A' * 1000]
]
FUZZ_BODIES = [
  '', 'A' * 10, 'B' * 100, 'C' * 1000, '{"key":"value"}', '<xml></xml>', '\x00\x01\x02', 'DROP TABLE users;', '🐍🐍🐍', '" OR 1=1 --']

def random_headers
  headers = {}
  FUZZ_HEADERS.sample(rand(1..FUZZ_HEADERS.size)).each do |k, v|
    headers[k] = v
  end
  headers
end

def random_body
  FUZZ_BODIES.sample
end

ITERATIONS.times do |i|
  method = HTTP_METHODS.sample
  path = FUZZ_PATHS.sample
  begin
    uri = URI::HTTPS.build(host: TARGET_HOST, port: TARGET_PORT, path: path)
  rescue URI::InvalidComponentError, URI::InvalidURIError => e
    puts "[#{i+1}] Skipping invalid path: #{path.inspect} (#{e.class}: #{e.message})"
    next
  end

  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = USE_SSL
  http.verify_mode = OpenSSL::SSL::VERIFY_NONE

  headers = random_headers
  body = %w[POST PUT PATCH].include?(method) ? random_body : nil

  request_class = Net::HTTP.const_get(method.capitalize) rescue Net::HTTP::Get
  request = request_class.new(uri.request_uri, headers)
  request.body = body if body

  puts "\n[#{i+1}] Sending #{method} #{uri}"
  puts "Headers: #{headers.inspect}"
  puts "Body: #{body.inspect}" if body

  begin
    response = http.request(request)
    puts "Response: #{response.code} #{response.message}"
    puts "Response body (first 200 chars): #{response.body[0,200].inspect}"
  rescue => e
    puts "Error: #{e.class} - #{e.message}"
  end
end
