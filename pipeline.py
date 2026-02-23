#import chunker
from chunker import chunker
#import mapper 
from mapper import mapper
#import reducer 
from reducer import reducer
#define pipe class with __init__
class Pipe: 
    def __init__(self, value): 
        self.value = value
    def __or__(self, func):
        return Pipe(func(self.value))
    #loop through chunks and apply mapper to each chunk
def map_chunks(chunks):
    return (mapper(chunk) for chunk in chunks)
#VERIFICATION 
try: 
    pipe = Pipe("cleaner_clinical.tsv") | chunker | map_chunks | reducer
    print(pipe.value)
except AssertionError as e:
    print(f"Verification error: {e}")    
except Exception as e:
    print(f"Pipeline error: {e}")
    raise