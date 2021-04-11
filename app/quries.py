def apt_list():
    return {
        "aggs" : {
            "apts": {
                "terms": {"field": "apt_name", "size": 9999999}
            }
        },
    "size":0
    }