# cinco

Install pyenv, and it should automagically use the python version specified in `.python-version`

Tooling is listed in dev-requirements.txt

For the pre-commit-config to work, make sure you're using rbenv, and have set `rbenv global 3.3.6` or higher ruby version. Rubocop pre-commit doesn't respect `rbenv local` or `.ruby-version` files, but does respect `rbenv global`, for some reason.

(The Ruby Version used by arclight is specified in `arclight/.ruby-version`)

## Caching

### Infrastructure Caching - CloudFront

#### OAC
- Error pages, S3 Assets, and Static Finding Aids all use the AWS managed cache policy called `CachingOptimized`. This policy caches pages with a Minimum TTL of 1 second, a Maximum TTL of 1 year, and a Default TTL of 24 hours (actual TTL is specified by the CloudFront origin - in this case always the production s3 bucket). Request headers, cookies, and query strings are *not* included in the cache key, therefore, if the same page is loaded twice but with different headers, cookies, or query strings, the page is treated as a cache hit the second time it is loaded.

When there is a cache miss and CloudFront must hit s3 for the page, there is no origin request policy specified for how CloudFront hits s3 (not sure what default behavior is)

- The Arclight Application uses a custom `CDL-UseOriginCacheControlHeaders-QueryStrings-no-cookies` cache policy. This policy again caches pages with a Minimum TTL of 1 second, a Maximum TTL of 1 year, and a Default TTL of 24 hours (actual TTL is specified by the Cloudfront origin - in this case, the Arclight Application). Request headers and query strings *are* included in the cache key, specifically the following headers: `origin`, `x-method-override`, `x-http-method`, `host`, and `x-http-method-override`. Cookies are *not* included in the cache key. This allows search results pages to be cached based on their specific search query (query string). `x-http-method`, `x-method-override`, and `x-http-method-override` allow for tunneling PUT and DELETE requests through GET and POST requests - this cache policy caches these tunneled use cases as different page requests. The request headers `host` and `origin` should always be oac.cdlib.org and https://oac.cdlib.org/, respectively.

When there is a cache miss and CloudFront must hit Arclight for the page, CloudFront passes on this request to the origin using the managed `AllViewer` origin request policy to send along all viewer headers, all cookies, and all query strings to the ALB origin.

#### OAC-STG
The same as OAC, except the Arclight Application uses the managed `UseOriginCacheControlHeaders-QueryStrings` cache policy, which is the same as the custom policy described above except that it also differentiates the cache key with any cookies sent in the response.

#### OAC Dashboard

TBD

### Application Caching - Arclight

Arclight uses Solid Cache (https://github.com/rails/solid_cache) for caching static finding aids, see the [Arclight Readme](/arclight/readme.md#caching-for-static-finding-aids) for details.

### Application Caching - CincoCtrl

TBD
