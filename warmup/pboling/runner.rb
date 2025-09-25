require 'rack'
require 'webrick'
require_relative 'fuzzer_lib'

# Load the Rack app from config.ru
app, _ = Rack::Builder.parse_file(File.expand_path('config.ru', __dir__))

server_thread = Thread.new do
  Rack::Handler::WEBrick.run(app, Port: 9292, AccessLog: [], Logger: WEBrick::Log.new('/dev/null'))
end

# Wait for the server to be ready
require 'net/http'
ready = false
10.times do
  begin
    res = Net::HTTP.get_response('localhost', '/', 9292)
    if res.is_a?(Net::HTTPSuccess) || res.is_a?(Net::HTTPRedirection) || res.code.to_i == 404
      ready = true
      break
    end
  rescue Errno::ECONNREFUSED, Errno::EHOSTUNREACH
    sleep 0.5
  end
end

unless ready
  puts 'Server did not start in time.'
  exit 1
end

fuzzer_thread = Thread.new do
  loop do
    Fuzzer.run(10) # Run 10 iterations per loop
    sleep 1
  end
end

trap('INT') do
  puts "\nShutting down..."
  fuzzer_thread.kill
  server_thread.kill
  exit
end

server_thread.join
fuzzer_thread.join
