import cf from 'cloudfront';

const kvsHandle = cf.kvs();

async function handler(event) {
  var request = event.request;
  var headers = request.headers;
  if (headers.host) { console.log("host header: " + headers.host.value) }

  // Redirect http(s)://oac4.cdlib.org/<path> to
  //          https://oac.cdlib.org
  if (headers.host && headers.host.value.startsWith('oac4.')) {

    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: { value: "https://oac.cdlib.org" }
      }
    };
  }


  // Redirect http(s)://www.oac.cdlib.org/<path> to
  //          https://oac.cdlib.org/<path>
  // (remove the www. subdomain)
  if (headers.host && headers.host.value.startsWith('www.')) {
    let newHost = headers.host.value.replace(/^www\./, '');
    let redirectUrl = 'https://' + newHost + request.uri;

    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: { value: redirectUrl }
      }
    };
  }

  // Redirect http(s)://findaid.oac.cdlib.org/<path> to
  //          https://oac.cdlib.org/<path>
  // (remove the findaid. subdomain)
  else if (headers.host && headers.host.value.startsWith('findaid.')) {
    let newHost = headers.host.value.replace(/^findaid\./, '');
    let redirectUrl = 'https://' + newHost + request.uri;

    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: { value: redirectUrl }
      }
    };
  }

  // Redirect http(s)://ark.cdlib.org/<ark_shoulder> to
  //          https://publishing.cdlib.org/ucpressebooks/view?docId=<ark_shoulder>
  // if the ark_shoulder exists in the kvs store
  else if (headers.host && headers.host.value.startsWith('ark')) {
    let uri = request.uri
    if (uri.endsWith("/")) {
        uri = uri.slice(0,-1)
    }
    let ark = uri.split("/").pop();
    const exists = await kvsHandle.exists(ark);
    if (exists) {
        let newHost = "publishing.cdlib.org";
        let redirectUrl = 'https://' + newHost + "/ucpressebooks/view?docId=" + ark;
        console.log("redirecting to: " + redirectUrl);
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                location: { value: redirectUrl }
            }
      }
    }
  }

  // Redirect http://texts.cdlib.org/view?docId=<ark_shoulder>&... to
  //          https://calisphere.org/item/ark:/13030/<ark_shoulder>/
  // (disregarding any other query parameters)
  else if (headers.host && headers.host.value.startsWith('texts.')) {
      let querystring = request.querystring;
      if (querystring && querystring.docId && querystring.docId.value) {
          let ark_shoulder = querystring.docId.value;
          ark_shoulder = ark_shoulder.split(';')[0];
          let newHost = "calisphere.org";
          let redirectUrl = 'https://' + newHost + "/item/ark:/13030/" + ark_shoulder + '/';
          console.log("redirecting to: " + redirectUrl);
          return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                location: { value: redirectUrl }
            }
          };
      }
  }

  // Redirect oac.cdlib.org/findaid/ark:%2F\d{5}%2F[a-zA-Z0-9]+(.*) to
  //          oac.cdlib.org/findaid/ark:/$1/$2$3
  else if (headers.host && headers.host.value === 'oac.cdlib.org') {
      let uri = request.uri;
      let arkEncodedPattern = /\/findaid\/ark:%2F(\d{5})%2F([a-zA-Z0-9]+)(.*)/;
      let match = uri.match(arkEncodedPattern);
      if (match) {
          let newUri = `/findaid/ark:/${match[1]}/${match[2]}${match[3]}`;
          let redirectUrl = 'https://' + headers.host.value + newUri;
          console.log("redirecting to: " + redirectUrl);
          return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                location: { value: redirectUrl }
            }
          };
      }
  }

  return request;
}
