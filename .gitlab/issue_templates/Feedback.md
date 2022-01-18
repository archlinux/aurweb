**NOTE:** This issue template is only applicable to FastAPI implementations
in the code-base, which only exists within the `pu` branch. If you wish to
file an issue for the current PHP implementation of aurweb, please file a
standard issue prefixed with `[Bug]` or `[Feature]`.


**Checklist**

- [ ] I have prefixed the issue title with `[Feedback]` along with a message
      pointing to the route or feature tested.
    - Example: `[Feedback] /packages/{name}`
- [ ] I have completed the [Changes](#changes) section.
- [ ] I have completed the [Bugs](#bugs) section.
- [ ] I have completed the [Improvements](#improvements) section.
- [ ] I have completed the [Summary](#summary) section.

### Changes

Please describe changes in user experience when compared to the PHP
implementation. This section can actually hold a lot of info if you
are up for it -- changes in routes, HTML rendering, back-end behavior,
etc.

If you cannot see any changes from your standpoint, include a short
statement about that fact.

### Bugs

Please describe any bugs you've experienced while testing the route
pertaining to this issue. A "perfect" bug report would include your
specific experience, what you expected to occur, and what happened
otherwise. If you can, please include output of `docker-compose logs fastapi`
with your report; especially if any unintended exceptions occurred.

### Improvements

If you've experienced improvements in the route when compared to PHP,
please do include those here. We'd like to know if users are noticing
these improvements and how they feel about them.

There are multiple routes with no improvements. For these, just include
a short sentence about the fact that you've experienced none.

### Summary

First: If you've gotten here and completed the [Changes](#changes),
[Bugs](#bugs), and [Improvements](#improvements) sections, we'd like
to thank you very much for your contribution and willingness to test.
We are not a company, and we are not a large team; any bit of assistance
here helps the project astronomically and moves us closer toward a
new release.

That being said: please include an overall summary of your experience
and how you felt about the current implementation which you're testing
in comparison with PHP (current aur.archlinux.org, or https://localhost:8443
through docker).

/label feedback
