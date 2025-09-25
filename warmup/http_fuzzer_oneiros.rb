require "net/http"
require "securerandom"

MAX_RUNS = 1_000

http = Net::HTTP.new("localhost")
http.start

MAX_RUNS.times do
  path_components = (1..rand(1..5)).map { SecureRandom.hex[0..rand(1..20)] }
  path = "/#{path_components.join("/")}"

  response = http.get(path)

  if response.code_type.is_a? Net::HTTPServerError
    puts "Got error #{response.code} for path #{path}"
    break
  end
ensure
  http.finish
end
