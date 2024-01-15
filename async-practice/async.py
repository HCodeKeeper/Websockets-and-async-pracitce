import asyncio
from time import sleep, time

# asyncio.coroutine's are not iterable while async syntax returns iterable from function

# https://stackoverflow.com/questions/47493369/differences-between-futures-in-python3-and-promises-in-es6#:~:text=64-,In%20both%20Python%20and%20ES6%2C%20await/async%20are%20based%20on,launch%20synchronous%20code%20chunks%20in%20separate%20threads%20via%20asyncio%20threadpool%20API),-Share
# Long story short: Future - placeholder for future results, Coroutine function is a generator of coroutines, which yields futures to the eventloop and then receives the future back and keeps iterating.
# Task is a coroutine and future combined. coroutine is a Task executor, and future is still the placeholder of the result of that coroutine. Usually created by eventloop when assigning the coroutine
# In order to input value to the generator we use yield , or  (yield).
"""
Example:

def generator():
    print("Started")
    while True:
        x = (yield)
        yield x*2

gen_obj = generator().next Because generator starts outside the yield loop. Otherwise gen_obj.send would be impossible
gen_obj.send(10) -> 20
"""

async def example():
    return "Something"


def generator():
    for i in range(10):
        yield i


gen_object = generator()
print(gen_object)
print(type(gen_object))

# Not really useful on its own
# A Future is just a placeholder of results of a coroutine, also can have a callback
future = asyncio.get_event_loop().create_future()
future.add_done_callback(lambda future: future.done)
future.set_result("Something")

#loop.create_task(future)


#my_future = asyncio.ensure_future(example_coroutine()) Now thats more useful



def async_without_control_releasing():
    async def sleeping_for_real():
        sleep(2) # not async and not giving out the control, which stops main thread and not letting other coroutines work. So it's actually sync now
        return "Done sleeping for 2 secs"


    print(asyncio.run(sleeping_for_real()))
    print("This should run after sleeping in async")


async def time_consuming_IO_operation():
    print("")


async def async_release_control():
    async def make_toasts():
        print("Making toasts")
        await asyncio.sleep(2)
        print("Toasts made")
        return True
    
    async def brew_coffee():
        print("Brewing coffee")
        await asyncio.sleep(2)
        print("Coffee made")
        return True

    # Creating courutines and wrapping them in a Future, that is scheduled in the event loop
    print("Running in .gather now")
    start=time()
    results = asyncio.gather(make_toasts(), brew_coffee())
    print(f"Is done: results.done()")
    print("Manually waiting 1 sec")
    await asyncio.sleep(1)
    print(f"Is done: {results.done()}")
    print("Waiting with await for the future to complete")
    start = time()
    await results
    end=time() - start
    print(f"Awaited {end} more seconds. Previously waited manually")
    if results.done() and not results.cancelled():
        print(results)
        print(results.result())
    else:
        print("Wasnt done in time or got cancelled")
        return
    


if __name__ == '__main__':
    #async_without_lock_releasing()

    # .run CREATES NEW EVENT LOOP! WATCH OUT AS IT WILL CREATE PROBLEMS WITH TYING FUTURES. And is designed for running from the main thread on function like main, which encapsulates everything
    asyncio.run(async_release_control())