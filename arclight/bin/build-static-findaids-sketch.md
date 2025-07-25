

# 1. Query for a list of big finding aids using curl

We have a $SOLR_URL in the container, already defined.

Here's the query:
```
$SOLR_URL/select?
   fq=total_component_count_is%3A[4501%20TO%20*]&
   indent=true&
   q.op=OR&
   q=level_ssim%3A%22Collection%22&
   sort=total_component_count_is%20desc&
   rows=300&
   fl=total_component_count_is,id
```

- add last indexed date to returned fields for use in s3 metadata

```curl $SOLR_URL...```

# 2. Start the rails server

It's not currently running, since we issued a command override to start
this container, so:

```/rails/bin/docker-entrypoint ./bin/rails server &```

# 3. Get the currently running application version

This isn't currently anywhere in our image, the codebase isn't even a straight git checkout, and git isn't installed either, so we can't even run a git command. TODO: add this to our image (and our footer, while we're at it)

# 3. For each item in our solr search results set

- get the last indexed date
- get the ark

```
curl http://0.0.0.0:3000/findaid/static/$ARK -o /tmp/static.html
aws s3 cp /tmp/static.html s3://$S3_BUCKET/static_findaids/$ARK --metadata ArclightVersion=VERSION,LastIndexed=$LAST_INDEXED_DATE
```

- throttle requests so we don't overload solr
- stash in $S3_BUCKET/static_findaids/ (/static/ is Django's static files! don't overwrite!)
