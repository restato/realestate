def apt_list():
    '''
    아파트 리스트
    '''
    return {
        "aggs": {
            "apts": {
                "terms": {"field": "apt_name", "size": 9999999}
            }
        },
        "size": 0
    }


def new_high():
    '''
    아파트 신고가
    '''
    return {
        "aggs": {
            "apt_name": {
                "terms": {
                    "field": "apt_name",
                    "order": {"_key": "asc"},
                    "size": 999999
                },
                "aggs": {
                    "raw_values": {
                        "top_hits": {
                            "sort": [{
                                "transaction_amount": {"order": "desc"}
                            }],
                            "_source": {
                                "includes": ["transaction_date", "transaction_amount", "dedicated_area"]
                            },
                            "size": 1
                        }
                    }
                }
            }
        },
        "size": 0
    }
