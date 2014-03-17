from transform import transform

def modify_proxy_request(request, log):
    # Fake the header to ensure that mathml is rendered
    request.headers['User-Agent'] = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.11) Gecko/20101013 Ubuntu/10.10 (maverick) Firefox/3.6.11'
    return request

