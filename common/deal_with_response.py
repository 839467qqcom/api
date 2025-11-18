import allure


def deal_with_res(data, res,reason):
    # 主要用到了allure.attach，在接口请求时可以把必要的信息存放到报告里查看
    # 一一把需要显示的内容获取到，然后使用attach存放到报告
    # 方法里的res就是后面接口请求的内容，data就算是入参报文
    
    # 请求的url
    request_url = str(res.request.url)
    allure.attach(request_url, "请求的url")

    # 请求的方法
    request_method = str(res.request.method)
    allure.attach(request_method, "请求的方法")

    # 请求的headers
    request_headers = str(res.request.headers)
    allure.attach(request_headers, "请求的headers")

    # 入参报文
    request_data = str(data)
    allure.attach(request_data, "入参报文")

    # 响应时间
    response_time = str(res.elapsed.total_seconds() * 1000)
    allure.attach(response_time, "响应时间")

    # 状态码
    status_code = str(res.status_code)
    allure.attach(status_code, "状态码")

    # 响应报文
    response_text = str(res.text)
    allure.attach(response_text, "响应报文")
    allure.attach(reason, "断言")