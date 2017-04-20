from twisted.internet import defer, reactor, error


class DelayError(Exception):
    pass


def get_defer(ret_val=None, wait_time=0):
    d = defer.Deferred()
    reactor.callLater(wait_time, d.callback, ret_val)
    return d


def delay_error(d1, exception_instance=DelayError(), wait_time=60):
    d = defer.Deferred()
    call_later = reactor.callLater(wait_time, delay_error_helper, d, exception_instance)
    d1.addCallback(delay_callback, call_later, d)
    d1.addErrback(delay_errback, call_later, d)
    return d


def delay_callback(result, call_later, d):
    try:
        call_later.cancel()
    except error.AlreadyCalled:
        pass
    if d.called:
        return result
    d.callback(result)
    return result


def delay_errback(result, call_later, d):
    try:
        call_later.cancel()
    except error.AlreadyCalled:
        pass
    if d.called:
        return result
    d.errback(result)
    return result


def delay_error_helper(d, exception_instance):
    if d.called:
        return
    d.errback(exception_instance)


@defer.inlineCallbacks
def defer_list(dlist, **kwargs):
    result = []
    for item in dlist:
        item = yield item
        result.append(item)
    defer.returnValue(result)


def branch_defer(defer_app):
    # this function is deprecated
    # try to use defer.inlinecallbacks instead of this function
    d_new = defer.Deferred()
    defer_app.addCallback(branch_defer_helper, d_new)
    defer_app.addErrback(branch_defer_helper_error, d_new)
    return d_new


def branch_defer_helper(result, d_new):
    d_new.callback(result)
    return result


def branch_defer_helper_error(result, d_new):
    d_new.errback(result)
    return result


def spread_function(result, callback, *args, **kwords):
    # this function is deprecated
    # try to use defer.inlinecallbacks instead of this function
    arg_list = list(result) + list(args)
    return callback(*arg_list, **kwords)
