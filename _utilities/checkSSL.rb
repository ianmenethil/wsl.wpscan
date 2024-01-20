require 'net/http'
uri = URI('https://www.howsmyssl.com/a/check')
response = Net::HTTP.get(uri)
puts response