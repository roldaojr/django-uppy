from urllib.parse import urlparse, parse_qs


def s3_storage_settings_from_url(url: str) -> dict:
    bucket_url = urlparse(url)
    params = parse_qs(bucket_url.query)
    options = {}
    proto = "https"
    if bucket_url.scheme.startswith("s3+"):
        proto = bucket_url.scheme.split("+", 1)[1]
    if bucket_url.path:
        path = bucket_url.path.lstrip("/")
        if "/" in path:
            bucket_name, location = bucket_url.path.lstrip("/").split("/", maxsplit=1)
            options["bucket_name"] = bucket_name
            options["location"] = location
        else:
            options["bucket_name"] = path
        if bucket_url.hostname:
            endpoint_url = f"{proto}://{bucket_url.hostname}"
            if bucket_url.port:
                endpoint_url += f":{bucket_url.port}"
            options["endpoint_url"] = endpoint_url
    else:
        options["bucket_name"] = bucket_url.hostname
    if bucket_url.username:
        options["access_key"] = bucket_url.username
    if bucket_url.password:
        options["secret_key"] = bucket_url.password
    options.update(params)
    return {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": options}
