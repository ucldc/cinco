// Configure your import map in config/importmap.rb. Read more: https://github.com/rails/importmap-rails
import "@hotwired/turbo-rails"
import "controllers"
import * as bootstrap from "bootstrap"
import githubAutoCompleteElement from "@github/auto-complete-element"
import Blacklight from "blacklight"

import "arclight"


// Debugging Matomo tracking

class _paq {
    static push(...args) {
        console.log("Matomo tracking:", ...args);
    }
}

// function to track a page view with Matomo
function trackMatomoPageView() {
    if (typeof _paq !== 'undefined') {
        console.log("Tracking page view with Matomo");
        _paq.push(['setReferrerUrl', document.referrer]);
        _paq.push(['setCustomUrl', location.href]);
        _paq.push(['setDocumentTitle', document.title]);

        // remove all previously assigned custom dimensions
        _paq.push(['deleteCustomDimension', 1]);
        _paq.push(['deleteCustomDimension', 2]);

        // add custom dimensions, if available
        var repoDimension = document.getElementById('matomo-repo');
        if (repoDimension) {
            _paq.push(['setCustomDimension', 1, repoDimension.getAttribute('data-repo-slug')]);
        }
        var collectionDimension = document.getElementById('matomo-collection');
        if (collectionDimension) {
            _paq.push(['setCustomDimension', 2, collectionDimension.getAttribute('data-ark')]);
        }
        _paq.push(['trackPageView']);
        _paq.push(['enableLinkTracking']);
    }
}

document.documentElement.addEventListener('turbo:load', function() {
    return function(e) {
        console.log(e);
        console.log("document.location: ", document.location);
        trackMatomoPageView();
    };
}());
