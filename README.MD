# IG Data Anonymizer

To build static HTML site:

```
shinylive export ./ site
```

To deploy on Netlify:

```
netlify deploy -d site
```

(Initilaization of Shiny and Netlify is required before building. Read their docs.)

## Notes

- `ig_dm_scraper` by @NaphatPi
- Do not touch the `requirements.txt`. It is Shiny-specific and should not include unnecessary dependencies.