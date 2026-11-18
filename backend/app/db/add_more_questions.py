import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import (
    QuestionBankItem, QuestionBankOption, QuestionDifficultyEnum,
    QuestionStatusEnum, User, RoleEnum
)

EXTRA_QUESTIONS = [
    # ------------------ PYTHON (18 more questions -> 30 total) ------------------
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "String Formatting",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which string formatting syntax introduced in Python 3.6 allows embedding expressions directly inside string literals?",
        "explanation": "f-strings (formatted string literals) prefixed with 'f' or 'F' evaluate expressions enclosed in curly braces at runtime.",
        "marks": 1,
        "tags": ["python", "strings", "f-strings"],
        "options": [
            {"key": "A", "text": "f-strings (e.g. f'{variable}')", "is_correct": True},
            {"key": "B", "text": "printf formatting (%s)", "is_correct": False},
            {"key": "C", "text": "str.format() method", "is_correct": False},
            {"key": "D", "text": "Template strings ($variable)", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Dictionary Methods",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How do you retrieve a dictionary value safely without raising a KeyError if the key is absent in Python?",
        "explanation": "The 'dict.get(key, default)' method returns the default value (or None) if the key does not exist, avoiding KeyError.",
        "marks": 1,
        "tags": ["python", "dictionaries", "safety"],
        "options": [
            {"key": "A", "text": "dict.get(key, default)", "is_correct": True},
            {"key": "B", "text": "dict[key]", "is_correct": False},
            {"key": "C", "text": "dict.fetch(key)", "is_correct": False},
            {"key": "D", "text": "dict.lookup(key)", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Type Conversion",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does 'bool([])' evaluate to in Python?",
        "explanation": "Empty collections (empty list, tuple, set, dict, string) evaluate to False in boolean contexts.",
        "marks": 1,
        "tags": ["python", "truthiness", "types"],
        "options": [
            {"key": "A", "text": "False", "is_correct": True},
            {"key": "B", "text": "True", "is_correct": False},
            {"key": "C", "text": "None", "is_correct": False},
            {"key": "D", "text": "TypeError", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Unpacking",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which operator is used to unpack positional arguments from a list or tuple into a function call in Python?",
        "explanation": "The single asterisk '*' unpacks positional arguments, while '**' unpacks dictionary keyword arguments.",
        "marks": 1,
        "tags": ["python", "unpacking", "syntax"],
        "options": [
            {"key": "A", "text": "*", "is_correct": True},
            {"key": "B", "text": "**", "is_correct": False},
            {"key": "C", "text": "...", "is_correct": False},
            {"key": "D", "text": "&", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Scope (LEGB)",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What order of namespaces does Python search when resolving an unqualified variable name?",
        "explanation": "Python follows the LEGB rule: Local -> Enclosing -> Global -> Built-in.",
        "marks": 1,
        "tags": ["python", "scope", "legb"],
        "options": [
            {"key": "A", "text": "Local -> Enclosing -> Global -> Built-in (LEGB)", "is_correct": True},
            {"key": "B", "text": "Global -> Local -> Enclosing -> Built-in", "is_correct": False},
            {"key": "C", "text": "Built-in -> Global -> Local", "is_correct": False},
            {"key": "D", "text": "Module -> Class -> Function", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Functional Programming",
        "subtopic": "Lambda & Filter",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does 'list(filter(None, [0, 1, False, 2, '', 3]))' return in Python?",
        "explanation": "Passing 'None' as the function to filter() filters out all elements that are falsy in boolean context, yielding [1, 2, 3].",
        "marks": 1,
        "tags": ["python", "filter", "functional"],
        "options": [
            {"key": "A", "text": "[1, 2, 3]", "is_correct": True},
            {"key": "B", "text": "[0, False, '']", "is_correct": False},
            {"key": "C", "text": "[0, 1, 2, 3]", "is_correct": False},
            {"key": "D", "text": "TypeError: 'NoneType' object is not callable", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Object Oriented Programming",
        "subtopic": "Inheritance & super()",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does 'super()' determine the next class in the hierarchy to call in Python multiple inheritance?",
        "explanation": "'super()' follows the C3 Linearization algorithm to determine the Method Resolution Order (MRO) accessible via Class.__mro__.",
        "marks": 1,
        "tags": ["python", "mro", "super", "c3"],
        "options": [
            {"key": "A", "text": "Using the C3 Linearization Method Resolution Order (MRO)", "is_correct": True},
            {"key": "B", "text": "Depth-first search traversing left-to-right strictly", "is_correct": False},
            {"key": "C", "text": "Alphabetical order of parent class names", "is_correct": False},
            {"key": "D", "text": "Timestamp of parent class compilation", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Standard Library",
        "subtopic": "collections.defaultdict",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What happens when a missing key is accessed in a 'collections.defaultdict(list)' in Python?",
        "explanation": "It automatically calls the default_factory callable (list()), inserts the resulting empty list under that key, and returns it.",
        "marks": 1,
        "tags": ["python", "collections", "defaultdict"],
        "options": [
            {"key": "A", "text": "It invokes list(), inserts the empty list at that key, and returns it", "is_correct": True},
            {"key": "B", "text": "It raises a KeyError", "is_correct": False},
            {"key": "C", "text": "It returns None without inserting anything", "is_correct": False},
            {"key": "D", "text": "It creates an immutable tuple", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Concurrency",
        "subtopic": "Multiprocessing vs Threading",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Why should CPU-intensive computation tasks in Python use 'multiprocessing' rather than 'threading'?",
        "explanation": "'multiprocessing' spawns separate OS processes, each with its own CPython interpreter and memory space, effectively bypassing the Global Interpreter Lock (GIL).",
        "marks": 1,
        "tags": ["python", "multiprocessing", "gil"],
        "options": [
            {"key": "A", "text": "Each process gets its own GIL and interpreter, enabling true multi-core parallelism", "is_correct": True},
            {"key": "B", "text": "Processes consume 90% less memory than OS threads", "is_correct": False},
            {"key": "C", "text": "Threading does not support exception handling", "is_correct": False},
            {"key": "D", "text": "Multiprocessing disables garbage collection for speed", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Metaprogramming",
        "subtopic": "Descriptors",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What distinguishes a 'Data Descriptor' from a 'Non-Data Descriptor' in Python?",
        "explanation": "A descriptor that defines '__set__' (or '__delete__') is a Data Descriptor, which takes precedence over instance dictionary (__dict__) lookups.",
        "marks": 1,
        "tags": ["python", "descriptors", "metaprogramming"],
        "options": [
            {"key": "A", "text": "A Data Descriptor defines __set__ (or __delete__), taking precedence over instance __dict__", "is_correct": True},
            {"key": "B", "text": "Non-Data Descriptors can only store SQLite database connections", "is_correct": False},
            {"key": "C", "text": "Data Descriptors cannot implement __get__", "is_correct": False},
            {"key": "D", "text": "Data Descriptors must be declared inside C extensions", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Weak References",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does 'weakref.ref(obj)' create in Python?",
        "explanation": "It creates a weak reference that does not increment the target object's reference count, allowing it to be garbage collected when other references disappear.",
        "marks": 1,
        "tags": ["python", "weakref", "memory"],
        "options": [
            {"key": "A", "text": "A reference that does not prevent the target object from being garbage collected", "is_correct": True},
            {"key": "B", "text": "A deep copy stored in swap space", "is_correct": False},
            {"key": "C", "text": "A read-only freeze of the object", "is_correct": False},
            {"key": "D", "text": "An atomic thread-safe lock wrapper", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Concurrency",
        "subtopic": "Async Generators",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Which dual protocols must an asynchronous generator implement in Python?",
        "explanation": "An asynchronous generator implements '__aiter__' and '__anext__', returning an awaitable that yields values asynchronously.",
        "marks": 1,
        "tags": ["python", "asyncio", "generators"],
        "options": [
            {"key": "A", "text": "__aiter__ and __anext__", "is_correct": True},
            {"key": "B", "text": "__iter__ and __next__", "is_correct": False},
            {"key": "C", "text": "__enter__ and __exit__", "is_correct": False},
            {"key": "D", "text": "__await__ and __call__", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Bytecode & Disassembly",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Which standard library module disassembles Python functions into their underlying CPython bytecode instructions?",
        "explanation": "The 'dis' module disassembles Python code objects into human-readable bytecode representations.",
        "marks": 1,
        "tags": ["python", "bytecode", "dis"],
        "options": [
            {"key": "A", "text": "dis", "is_correct": True},
            {"key": "B", "text": "inspect", "is_correct": False},
            {"key": "C", "text": "types", "is_correct": False},
            {"key": "D", "text": "ast", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "ContextVar",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What problem does the 'contextvars' module solve in modern Python asynchronous programming?",
        "explanation": "'contextvars' provides context-local storage that works across asynchronous tasks and coroutines, replacing thread-local storage in asyncio.",
        "marks": 1,
        "tags": ["python", "asyncio", "contextvars"],
        "options": [
            {"key": "A", "text": "Context-local storage that correctly tracks state across asynchronous tasks and coroutines", "is_correct": True},
            {"key": "B", "text": "Hardware encryption of coroutine memory blocks", "is_correct": False},
            {"key": "C", "text": "Dynamic compilation of Cython speedups at runtime", "is_correct": False},
            {"key": "D", "text": "Inter-process semaphore synchronization", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Walrus Operator",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does the Walrus operator (':=') introduced in Python 3.8 allow you to do?",
        "explanation": "The walrus operator allows assignment expressions, assigning values to variables inside larger expressions (such as while loops or if statements).",
        "marks": 1,
        "tags": ["python", "walrus", "syntax"],
        "options": [
            {"key": "A", "text": "Assign values to variables inside expressions (e.g. while chunk := file.read())", "is_correct": True},
            {"key": "B", "text": "Perform strict type casting like TypeScript 'as'", "is_correct": False},
            {"key": "C", "text": "Declare constants that cannot be reassigned", "is_correct": False},
            {"key": "D", "text": "Compare both value and memory address simultaneously", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Pattern Matching",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which keyword pair introduced Structural Pattern Matching in Python 3.10?",
        "explanation": "Python 3.10 introduced structural pattern matching via 'match' and 'case' statements.",
        "marks": 1,
        "tags": ["python", "pattern-matching", "match-case"],
        "options": [
            {"key": "A", "text": "match and case", "is_correct": True},
            {"key": "B", "text": "switch and case", "is_correct": False},
            {"key": "C", "text": "select and when", "is_correct": False},
            {"key": "D", "text": "pattern and evaluate", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "itertools",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which function in 'itertools' produces the Cartesian product of input iterables?",
        "explanation": "itertools.product() computes the Cartesian product of input iterables, equivalent to nested for-loops.",
        "marks": 1,
        "tags": ["python", "itertools", "cartesian"],
        "options": [
            {"key": "A", "text": "itertools.product()", "is_correct": True},
            {"key": "B", "text": "itertools.combinations()", "is_correct": False},
            {"key": "C", "text": "itertools.permutations()", "is_correct": False},
            {"key": "D", "text": "itertools.chain()", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "functools.lru_cache",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does the '@functools.lru_cache' decorator do in Python?",
        "explanation": "It wraps a function with a Least Recently Used (LRU) memoizing callable, caching return values based on call arguments.",
        "marks": 1,
        "tags": ["python", "functools", "caching", "lru"],
        "options": [
            {"key": "A", "text": "Memoizes function return values up to a maxsize using an LRU eviction policy", "is_correct": True},
            {"key": "B", "text": "Compiles the function into native machine code", "is_correct": False},
            {"key": "C", "text": "Runs the function periodically on a background thread", "is_correct": False},
            {"key": "D", "text": "Restricts function calls to one execution per second", "is_correct": False}
        ]
    },

    # ------------------ JAVASCRIPT (17 more questions -> 30 total) ------------------
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "NaN Comparison",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the result of evaluating 'NaN === NaN' in JavaScript?",
        "explanation": "According to IEEE 754 floating-point standards adopted by JavaScript, NaN is never equal to anything, including itself. Number.isNaN() or Object.is() must be used.",
        "marks": 1,
        "tags": ["javascript", "nan", "equality"],
        "options": [
            {"key": "A", "text": "false", "is_correct": True},
            {"key": "B", "text": "true", "is_correct": False},
            {"key": "C", "text": "undefined", "is_correct": False},
            {"key": "D", "text": "TypeError", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Optional Chaining",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does the optional chaining operator '?.' do in JavaScript (e.g. user?.profile?.name)?",
        "explanation": "It safely accesses deeply nested object properties, immediately short-circuiting to 'undefined' if an intermediate reference is nullish (null or undefined) instead of throwing a TypeError.",
        "marks": 1,
        "tags": ["javascript", "optional-chaining", "syntax"],
        "options": [
            {"key": "A", "text": "Short-circuits to undefined if any intermediate reference is null or undefined without throwing TypeError", "is_correct": True},
            {"key": "B", "text": "Prompts the user for missing input in the browser", "is_correct": False},
            {"key": "C", "text": "Assigns a default empty string to undefined properties", "is_correct": False},
            {"key": "D", "text": "Encodes property names into URL search params", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Nullish Coalescing",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How does the Nullish Coalescing operator '??' differ from the Logical OR operator '||'?",
        "explanation": "'??' only falls back to the right-hand operand when the left-hand operand is null or undefined, preserving falsy values like 0, '', and false.",
        "marks": 1,
        "tags": ["javascript", "nullish-coalescing", "operators"],
        "options": [
            {"key": "A", "text": "'??' only falls back on null or undefined; '||' falls back on any falsy value (0, '', false)", "is_correct": True},
            {"key": "B", "text": "'??' works only with strings, while '||' works with booleans", "is_correct": False},
            {"key": "C", "text": "'??' is deprecated in ES2020", "is_correct": False},
            {"key": "D", "text": "'??' returns a boolean, while '||' returns an object", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Arrays",
        "subtopic": "Destructuring",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How can you swap two variables 'a' and 'b' without a temporary variable using ES6 syntax?",
        "explanation": "Array destructuring allows '[a, b] = [b, a]', swapping variables in a single expression.",
        "marks": 1,
        "tags": ["javascript", "destructuring", "es6"],
        "options": [
            {"key": "A", "text": "[a, b] = [b, a];", "is_correct": True},
            {"key": "B", "text": "swap(a, b);", "is_correct": False},
            {"key": "C", "text": "{a, b} = {b, a};", "is_correct": False},
            {"key": "D", "text": "a.swap(b);", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Async & Promises",
        "subtopic": "Promise.all vs Promise.allSettled",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the key advantage of 'Promise.allSettled' over 'Promise.all'?",
        "explanation": "'Promise.all' rejects immediately when any promise rejects (fail-fast), whereas 'Promise.allSettled' waits for all promises to finish and returns an array of outcome objects.",
        "marks": 1,
        "tags": ["javascript", "promises", "allsettled"],
        "options": [
            {"key": "A", "text": "Promise.allSettled waits for all promises to complete regardless of rejections, returning outcome statuses for each", "is_correct": True},
            {"key": "B", "text": "Promise.allSettled executes promises in sequential synchronous order", "is_correct": False},
            {"key": "C", "text": "Promise.allSettled ignores rejected promises completely", "is_correct": False},
            {"key": "D", "text": "Promise.allSettled only works in Node.js server environments", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Functions & Context",
        "subtopic": "Call vs Apply vs Bind",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the difference between Function.prototype.call() and Function.prototype.apply()?",
        "explanation": "call() takes arguments individually comma-separated, while apply() takes arguments as a single array or array-like object.",
        "marks": 1,
        "tags": ["javascript", "call", "apply", "this"],
        "options": [
            {"key": "A", "text": "call() accepts arguments as a comma-separated list; apply() accepts arguments as an array", "is_correct": True},
            {"key": "B", "text": "call() returns a new function; apply() invokes immediately", "is_correct": False},
            {"key": "C", "text": "apply() binds 'this' permanently, while call() is temporary", "is_correct": False},
            {"key": "D", "text": "call() is asynchronous, while apply() is synchronous", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Objects",
        "subtopic": "Object.freeze vs Object.seal",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does Object.freeze() prevent that Object.seal() does NOT?",
        "explanation": "Object.seal() allows modifying existing writable property values. Object.freeze() makes all existing properties non-writable, preventing value modification.",
        "marks": 1,
        "tags": ["javascript", "objects", "freeze", "seal"],
        "options": [
            {"key": "A", "text": "Object.freeze prevents modifying existing property values; Object.seal permits changing existing values", "is_correct": True},
            {"key": "B", "text": "Object.freeze prevents garbage collection; Object.seal does not", "is_correct": False},
            {"key": "C", "text": "Object.seal works recursively; Object.freeze is shallow", "is_correct": False},
            {"key": "D", "text": "There is no difference between them", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "DOM & Events",
        "subtopic": "Event Delegation",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does Event Delegation work in client-side JavaScript?",
        "explanation": "Event delegation attaches a single event listener to a common parent element, leveraging event bubbling to handle events dispatched from dynamic children.",
        "marks": 1,
        "tags": ["javascript", "dom", "events", "delegation"],
        "options": [
            {"key": "A", "text": "Attaching a single listener to a parent element and taking advantage of event bubbling to catch child events", "is_correct": True},
            {"key": "B", "text": "Delegating DOM manipulation tasks to Web Worker background threads", "is_correct": False},
            {"key": "C", "text": "Preventing events from firing more than once per minute", "is_correct": False},
            {"key": "D", "text": "Routing events across WebSocket connections to the server", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Iterators & Generators",
        "subtopic": "Symbol.iterator",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How can an object be made iterable so it can be consumed by 'for...of' loops in JavaScript?",
        "explanation": "By implementing a method under the well-known symbol '[Symbol.iterator]()' that returns an object conforming to the Iterator protocol (with a .next() method).",
        "marks": 1,
        "tags": ["javascript", "iterators", "symbol-iterator"],
        "options": [
            {"key": "A", "text": "By defining a method keyed by [Symbol.iterator] that returns an iterator object with a next() method", "is_correct": True},
            {"key": "B", "text": "By adding an '__iterable__' property set to true", "is_correct": False},
            {"key": "C", "text": "By inheriting from Array.prototype", "is_correct": False},
            {"key": "D", "text": "By calling Object.makeIterable(obj)", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Memory & V8",
        "subtopic": "Hidden Classes & Inline Caching",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why does dynamically adding properties in differing orders across instances degrade V8 JavaScript performance?",
        "explanation": "V8 generates internal 'hidden classes' (shapes) based on property creation order. Adding properties in different orders creates diverging hidden class transition trees, deoptimizing inline caches.",
        "marks": 1,
        "tags": ["javascript", "v8", "hidden-classes", "performance"],
        "options": [
            {"key": "A", "text": "It causes hidden class (shape) divergence, disabling V8's monomorphic inline cache optimizations", "is_correct": True},
            {"key": "B", "text": "It forces V8 to switch into pure interpretive bytecode mode permanently", "is_correct": False},
            {"key": "C", "text": "It triggers garbage collection on every single object instantiation", "is_correct": False},
            {"key": "D", "text": "It causes memory fragmentation by allocating 64KB pages per object", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Concurrency",
        "subtopic": "SharedArrayBuffer & Atomics",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does the 'Atomics.wait()' method do in JavaScript Web Workers?",
        "explanation": "Atomics.wait() verifies that a shared memory location contains an expected value and puts the worker thread to sleep until awakened via Atomics.notify() or timeout.",
        "marks": 1,
        "tags": ["javascript", "atomics", "sharedarraybuffer", "concurrency"],
        "options": [
            {"key": "A", "text": "Blocks a worker thread until notified via Atomics.notify() or a timeout occurs", "is_correct": True},
            {"key": "B", "text": "Pauses the main UI thread during network fetch requests", "is_correct": False},
            {"key": "C", "text": "Halts the V8 garbage collector", "is_correct": False},
            {"key": "D", "text": "Waits for an IndexedDB transaction to commit", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Tagged Template Literals",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What arguments does a Tagged Template Literal function receive in JavaScript?",
        "explanation": "The tag function receives an array of static string literals as its first argument, followed by the evaluated interpolation expressions as subsequent arguments.",
        "marks": 1,
        "tags": ["javascript", "template-literals", "tagged-templates"],
        "options": [
            {"key": "A", "text": "An array of static string chunks as the first argument, followed by the interpolated values", "is_correct": True},
            {"key": "B", "text": "A compiled AST node tree representing the template", "is_correct": False},
            {"key": "C", "text": "A single concatenated string with HTML entities escaped", "is_correct": False},
            {"key": "D", "text": "A Promise resolving to a DOM node", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Generator Delegating",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does the 'yield*' expression accomplish inside a JavaScript generator function?",
        "explanation": "'yield*' delegates iteration to another generator or iterable object, yielding its values one by one until exhausted.",
        "marks": 1,
        "tags": ["javascript", "generators", "yield-star"],
        "options": [
            {"key": "A", "text": "Delegates iteration to another iterable or generator function", "is_correct": True},
            {"key": "B", "text": "Multiplies the yielded value by the next argument", "is_correct": False},
            {"key": "C", "text": "Terminates the generator immediately and returns null", "is_correct": False},
            {"key": "D", "text": "Yields values strictly in parallel Web Worker threads", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "BigInt",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Why was the BigInt primitive introduced in JavaScript?",
        "explanation": "JavaScript's standard Number type is an IEEE 754 double precision float, which can only safely represent integers up to Number.MAX_SAFE_INTEGER (2^53 - 1). BigInt represents arbitrary precision integers.",
        "marks": 1,
        "tags": ["javascript", "bigint", "numbers"],
        "options": [
            {"key": "A", "text": "To safely represent integers larger than 2^53 - 1 with arbitrary precision", "is_correct": True},
            {"key": "B", "text": "To accelerate 3D vector matrix calculations in WebGL", "is_correct": False},
            {"key": "C", "text": "To replace standard floating point arithmetic in CSS", "is_correct": False},
            {"key": "D", "text": "To prevent stack overflow errors during recursion", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Currying",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is 'Currying' in JavaScript functional programming?",
        "explanation": "Currying transforms a function taking multiple arguments into a sequence of unary functions, each taking a single argument.",
        "marks": 1,
        "tags": ["javascript", "functional", "currying"],
        "options": [
            {"key": "A", "text": "Transforming a multi-argument function into a chain of single-argument functions", "is_correct": True},
            {"key": "B", "text": "Caching asynchronous API responses in browser memory", "is_correct": False},
            {"key": "C", "text": "Mutating global state variables inside nested loops", "is_correct": False},
            {"key": "D", "text": "Binding event handlers dynamically to button clicks", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Modules",
        "subtopic": "ES Modules vs CommonJS",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the primary difference in how ES Modules (import/export) and CommonJS (require) are loaded?",
        "explanation": "ES Modules are statically analyzed and parsed before code execution, enabling tree-shaking; CommonJS modules are loaded synchronously and dynamically at runtime.",
        "marks": 1,
        "tags": ["javascript", "esm", "commonjs", "modules"],
        "options": [
            {"key": "A", "text": "ES Modules are statically parsed at compile time; CommonJS modules are loaded dynamically at runtime", "is_correct": True},
            {"key": "B", "text": "CommonJS only runs in browsers, while ESM only runs in Node.js", "is_correct": False},
            {"key": "C", "text": "ES Modules cannot export functions or classes", "is_correct": False},
            {"key": "D", "text": "CommonJS supports top-level await, while ESM does not", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "DOM",
        "subtopic": "MutationObserver",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the purpose of the MutationObserver API in modern web development?",
        "explanation": "MutationObserver provides a performant mechanism to watch for changes made to the DOM tree (child additions, attribute modifications, text updates) asynchronously without polling.",
        "marks": 1,
        "tags": ["javascript", "dom", "mutation-observer"],
        "options": [
            {"key": "A", "text": "Asynchronously monitors DOM tree changes (attributes, nodes, text) without polling", "is_correct": True},
            {"key": "B", "text": "Monitors network packets in the browser DevTools", "is_correct": False},
            {"key": "C", "text": "Watches Redux store actions in real time", "is_correct": False},
            {"key": "D", "text": "Calculates battery status and CPU temperature", "is_correct": False}
        ]
    }
]

def add_extra():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == RoleEnum.ADMIN).first()
        admin_id = admin.id if admin else None

        added = 0
        for item in EXTRA_QUESTIONS:
            exists = db.query(QuestionBankItem).filter(
                QuestionBankItem.question_text == item["question_text"]
            ).first()
            if exists:
                continue

            q = QuestionBankItem(
                technology=item["technology"],
                topic=item["topic"],
                subtopic=item.get("subtopic"),
                difficulty=item["difficulty"],
                question_type="SINGLE_CORRECT_MCQ",
                question_text=item["question_text"],
                explanation=item.get("explanation"),
                marks=item.get("marks", 1),
                tags=item.get("tags", []),
                is_global=True,
                created_by_user_id=admin_id,
                status=QuestionStatusEnum.ACTIVE,
                usage_count=0
            )
            db.add(q)
            db.flush()

            for opt in item["options"]:
                o = QuestionBankOption(
                    question_bank_id=q.id,
                    option_key=opt["key"],
                    option_text=opt["text"],
                    is_correct=opt["is_correct"]
                )
                db.add(o)
            added += 1

        db.commit()
        print(f"Added {added} extra high quality questions to database!")
    finally:
        db.close()

if __name__ == "__main__":
    add_extra()
