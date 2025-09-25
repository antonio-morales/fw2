require 'rack'

app = Proc.new do |env|
  req = Rack::Request.new(env)
  method = req.request_method
  path = req.path_info

  case path
  when '/'
    [200, { 'Content-Type' => 'text/plain' }, ["Root endpoint: #{method}"]]
  when '/test'
    [200, { 'Content-Type' => 'text/plain' }, ["Test endpoint: #{method}"]]
  when '/fuzz'
    [200, { 'Content-Type' => 'text/plain' }, ["Fuzz endpoint: #{method}"]]
  when '/random'
    [200, { 'Content-Type' => 'text/plain' }, ["Random endpoint: #{method}"]]
  when '/api'
    [200, { 'Content-Type' => 'text/plain' }, ["API endpoint: #{method}"]]
  when '/v1/resource'
    [200, { 'Content-Type' => 'text/plain' }, ["Resource endpoint: #{method}"]]
  else
    [404, { 'Content-Type' => 'text/plain' }, ["Not found: #{path}"]]
  end
end

run app

