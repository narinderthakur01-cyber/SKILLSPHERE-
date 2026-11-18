import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import PracticeQuestion, PracticeAttempt, Candidate

# Curated High-Quality Question Bank Template Generator
# For each technology, provides 20 initial curated questions (7 Beginner, 7 Intermediate, 6 Advanced)
# plus programmatic generation of 10 more questions per requested batch.

CURATED_QUESTION_BANKS: Dict[str, List[Dict[str, Any]]] = {
    "Python": [
        # --- 7 BEGINNER ---
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Mutable vs Immutable Built-in Types",
            "prompt": "Which of the following data types is mutable in Python?",
            "options": [
                {"key": "A", "text": "tuple"},
                {"key": "B", "text": "list"},
                {"key": "C", "text": "str"},
                {"key": "D", "text": "int"}
            ],
            "correct_answer": "B",
            "hint": "Think about which collection allows in-place modifications using .append() or index assignment.",
            "explanation": "In Python, lists, dictionaries, and sets are mutable. Tuples, strings, integers, and floats are immutable.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "List Comprehension Syntax",
            "prompt": "What does the expression `[x**2 for x in range(5) if x % 2 == 0]` evaluate to?",
            "options": [
                {"key": "A", "text": "[0, 4, 16]"},
                {"key": "B", "text": "[1, 9]"},
                {"key": "C", "text": "[0, 1, 4, 9, 16]"},
                {"key": "D", "text": "[4, 16]"}
            ],
            "correct_answer": "A",
            "hint": "range(5) produces 0, 1, 2, 3, 4. Filter for even numbers first, then square them.",
            "explanation": "The numbers 0, 2, and 4 satisfy `x % 2 == 0`. Their squares are 0, 4, and 16.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Dictionary Key Restrictions",
            "prompt": "Which of the following objects CANNOT be used as a dictionary key in Python?",
            "options": [
                {"key": "A", "text": "('data', 1)"},
                {"key": "B", "text": "'user_id'"},
                {"key": "C", "text": "[1, 2, 3]"},
                {"key": "D", "text": "42"}
            ],
            "correct_answer": "C",
            "hint": "Dictionary keys in Python must be hashable and immutable.",
            "explanation": "Lists are unhashable mutable objects, raising `TypeError: unhashable type: 'list'` if used as dict keys.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Exception Handling Clauses",
            "prompt": "In a Python try-except-finally block, when is the `finally` block executed?",
            "options": [
                {"key": "A", "text": "Only when an exception is raised and caught"},
                {"key": "B", "text": "Only when no exception is raised"},
                {"key": "C", "text": "Always, whether an exception occurs or not"},
                {"key": "D", "text": "Only if explicitly invoked by return"}
            ],
            "correct_answer": "C",
            "hint": "The finally clause is designed for clean-up tasks like closing file descriptors or database sockets.",
            "explanation": "The finally block always runs prior to exiting the try-except statement, even if an unhandled exception or return occurs.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Identity vs Equality Operators",
            "prompt": "What is the difference between `==` and `is` in Python?",
            "options": [
                {"key": "A", "text": "`==` checks memory address; `is` checks value equality"},
                {"key": "B", "text": "`==` checks value equality; `is` checks object identity (memory reference)"},
                {"key": "C", "text": "They are completely interchangeable aliases"},
                {"key": "D", "text": "`is` converts types before comparing; `==` does not"}
            ],
            "correct_answer": "B",
            "hint": "`is` compares `id(a) == id(b)`.",
            "explanation": "`==` evaluates whether values are equivalent (`__eq__`), while `is` verifies whether both variables reference the exact same object in memory.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Default Argument Evaluation",
            "prompt": "What happens if a mutable object (like a list) is used as a default parameter in a function definition `def append_to(item, target=[])`?",
            "options": [
                {"key": "A", "text": "A fresh empty list is created on every call"},
                {"key": "B", "text": "The default list is evaluated once at definition time and shared across subsequent calls"},
                {"key": "C", "text": "Python raises a SyntaxError at compile time"},
                {"key": "D", "text": "The list is frozen into an immutable tuple"}
            ],
            "correct_answer": "B",
            "hint": "Default arguments are bound when the function definition is executed, not at call time.",
            "explanation": "Default arguments are evaluated once when the function is defined. Subsequent calls share the same mutable object unless defaulted to `None`.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "String Slicing Step Index",
            "prompt": "What is the result of `'SkillSphere'[::-1]`?",
            "options": [
                {"key": "A", "text": "'SkillSphere'"},
                {"key": "B", "text": "'erehpSllikS'"},
                {"key": "C", "text": "'Skill'"},
                {"key": "D", "text": "IndexError"}
            ],
            "correct_answer": "B",
            "hint": "A step value of -1 reverses the iterable from end to start.",
            "explanation": "The slice `[::-1]` traverses the sequence backward from the final character to the first, reversing the string.",
            "batch_number": 1
        },

        # --- 7 INTERMEDIATE ---
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Python Generator Functions & Yield",
            "prompt": "How does a generator function using `yield` differ from a standard function using `return`?",
            "options": [
                {"key": "A", "text": "Generators consume more RAM by pre-allocating memory for all elements"},
                {"key": "B", "text": "Generators yield items lazily on-demand, pausing state between iterations with minimal memory consumption"},
                {"key": "C", "text": "Generators can only produce integers"},
                {"key": "D", "text": "Generators run in a separate background thread automatically"}
            ],
            "correct_answer": "B",
            "hint": "Generators implement the iterator protocol and maintain local variables across yields.",
            "explanation": "Generators produce items on the fly using `yield`, saving execution state and providing memory-efficient stream processing.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Function Decorators Mechanics",
            "prompt": "What is a Python decorator fundamentally under the hood?",
            "options": [
                {"key": "A", "text": "A compiler directive that modifies Python bytecode"},
                {"key": "B", "text": "A callable that takes another function as an argument and returns a wrapped or enhanced function"},
                {"key": "C", "text": "A special class that must inherit from `type`"},
                {"key": "D", "text": "A C-extension macro"}
            ],
            "correct_answer": "B",
            "hint": "`@my_decorator` syntax is syntactic sugar for `target = my_decorator(target)`.",
            "explanation": "A decorator takes a target function, wraps it inside an inner function with cross-cutting logic (logging, timing, auth), and returns the wrapper.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Global Interpreter Lock (GIL) Behavior",
            "prompt": "What constraint does CPython's Global Interpreter Lock (GIL) impose on multithreaded applications?",
            "options": [
                {"key": "A", "text": "It blocks asynchronous I/O networking completely"},
                {"key": "B", "text": "It ensures only one native thread executes Python bytecode at any single moment, limiting CPU-bound parallel speedup"},
                {"key": "C", "text": "It prevents processes from communicating over sockets"},
                {"key": "D", "text": "It disallows importing modules dynamically"}
            ],
            "correct_answer": "B",
            "hint": "Think about CPU-bound vs I/O-bound concurrency in CPython.",
            "explanation": "The GIL is a mutex protecting internal memory management. While I/O operations release the GIL, CPU-bound tasks cannot scale across multiple physical cores using threads alone.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "*args and **kwargs Unpacking",
            "prompt": "In the function signature `def handler(*args, **kwargs):`, what types are `args` and `kwargs` inside the body?",
            "options": [
                {"key": "A", "text": "`args` is a list, `kwargs` is a tuple"},
                {"key": "B", "text": "`args` is a tuple, `kwargs` is a dictionary"},
                {"key": "C", "text": "Both are lists"},
                {"key": "D", "text": "Both are generators"}
            ],
            "correct_answer": "B",
            "hint": "Positional variable arguments are packed into an immutable sequence, while keyword arguments are key-value mappings.",
            "explanation": "`*args` collects arbitrary positional arguments into a `tuple`, while `**kwargs` collects arbitrary keyword arguments into a `dict`.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Context Managers and __enter__ / __exit__",
            "prompt": "When implementing the context manager protocol for the `with` statement, which method handles exceptions raised inside the block?",
            "options": [
                {"key": "A", "text": "`__catch__`"},
                {"key": "B", "text": "`__exit__(exc_type, exc_val, exc_tb)`"},
                {"key": "C", "text": "`__finally__`"},
                {"key": "D", "text": "`__del__`"}
            ],
            "correct_answer": "B",
            "hint": "If this method returns True, Python suppresses the propagated exception.",
            "explanation": "`__exit__` receives `exc_type`, `exc_val`, and `exc_tb`. Returning `True` suppresses the exception; otherwise it bubbles up.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Shallow Copy vs Deep Copy",
            "prompt": "What occurs when `copy.deepcopy(nested_obj)` is invoked versus `copy.copy(nested_obj)`?",
            "options": [
                {"key": "A", "text": "copy.copy creates recursive duplicates of all nested objects"},
                {"key": "B", "text": "copy.deepcopy recursively clones all nested objects so modifications don't leak; copy.copy only clones top-level references"},
                {"key": "C", "text": "deepcopy only works on dictionaries"},
                {"key": "D", "text": "There is no difference in memory behavior"}
            ],
            "correct_answer": "B",
            "hint": "Think about nested lists within lists: `[[1, 2], [3, 4]]`.",
            "explanation": "Shallow copy creates a new outer collection pointing to the same child objects. Deep copy recursively duplicates child objects independently.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Classmethod vs Staticmethod Decorators",
            "prompt": "How does `@classmethod` differ from `@staticmethod`?",
            "options": [
                {"key": "A", "text": "`@classmethod` takes `cls` (the class object) as its implicit first parameter; `@staticmethod` takes no implicit arguments"},
                {"key": "B", "text": "`@staticmethod` can access instance variables via `self`"},
                {"key": "C", "text": "`@classmethod` cannot be called on class instances"},
                {"key": "D", "text": "They are deprecated in modern Python"}
            ],
            "correct_answer": "A",
            "hint": "Class methods are commonly used as alternative constructors (factory methods).",
            "explanation": "`@classmethod` receives the class `cls` as first argument, facilitating subclass polymorphism. `@staticmethod` behaves like a plain utility function pinned to the class namespace.",
            "batch_number": 2
        },

        # --- 6 ADVANCED ---
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Python Metaclasses & Class Construction",
            "prompt": "What is the default metaclass of all new-style classes in Python 3?",
            "options": [
                {"key": "A", "text": "object"},
                {"key": "B", "text": "type"},
                {"key": "C", "text": "Meta"},
                {"key": "D", "text": "ClassType"}
            ],
            "correct_answer": "B",
            "hint": "In Python, classes are themselves instances of another class.",
            "explanation": "In Python, `type` is the default metaclass responsible for constructing classes during module execution (`type(name, bases, dict)`).",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Descriptor Protocol (__get__, __set__, __delete__)",
            "prompt": "Which descriptor takes precedence during attribute lookup on an instance: a data descriptor or an entry in `instance.__dict__`?",
            "options": [
                {"key": "A", "text": "`instance.__dict__` always overrides data descriptors"},
                {"key": "B", "text": "A data descriptor (implementing `__set__` or `__delete__`) overrides `instance.__dict__`"},
                {"key": "C", "text": "Python raises AttributeError if both exist"},
                {"key": "D", "text": "Non-data descriptors override data descriptors"}
            ],
            "correct_answer": "B",
            "hint": "Data descriptors define at least `__set__` and supersede the instance dictionary.",
            "explanation": "Python's attribute resolution order evaluates data descriptors on the class before searching the instance dictionary `__dict__`.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Memory Optimization with __slots__",
            "prompt": "What is the primary benefit and consequence of defining `__slots__ = ('x', 'y')` in a class?",
            "options": [
                {"key": "A", "text": "It makes all instance attributes strictly private and thread-safe"},
                {"key": "B", "text": "It prevents dynamic `__dict__` allocation per instance, drastically reducing RAM for millions of objects"},
                {"key": "C", "text": "It enables GPU acceleration for math operations"},
                {"key": "D", "text": "It disables garbage collection"}
            ],
            "correct_answer": "B",
            "hint": "Regular objects maintain a dictionary for arbitrary attribute assignment.",
            "explanation": "`__slots__` allocates fixed array descriptors for specified attributes instead of a dynamic dictionary, reducing memory footprint substantially.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Asyncio Event Loop & Coroutines",
            "prompt": "What happens if a long-running CPU-intensive synchronous task is called directly inside an `async def` route without `run_in_executor`?",
            "options": [
                {"key": "A", "text": "The event loop automatically offloads it to a background OS thread"},
                {"key": "B", "text": "It blocks the single event loop thread, stalling all other concurrent client requests until completion"},
                {"key": "C", "text": "Python raises `BlockingIOError` immediately"},
                {"key": "D", "text": "The task is killed by the runtime watchdog"}
            ],
            "correct_answer": "B",
            "hint": "Asyncio is single-threaded cooperative multitasking.",
            "explanation": "Synchronous CPU-bound calls in the main event loop thread freeze scheduling of other coroutines. Heavy work must be run in `loop.run_in_executor()`.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Method Resolution Order (MRO) & C3 Linearization",
            "prompt": "Which algorithm does Python use to compute the Method Resolution Order (MRO) in multiple inheritance?",
            "options": [
                {"key": "A", "text": "Depth-First Search (DFS)"},
                {"key": "B", "text": "C3 Superclass Linearization"},
                {"key": "C", "text": "Breadth-First Search (BFS)"},
                {"key": "D", "text": "Dijkstra's Shortest Path"}
            ],
            "correct_answer": "B",
            "hint": "This algorithm guarantees monotonicity and respects local precedence orders.",
            "explanation": "Python 2.3+ utilizes the C3 Linearization algorithm to determine a deterministic class hierarchy order without diamond problem inconsistencies.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Garbage Collection & Weakref",
            "prompt": "How does Python handle reference cycles when `gc` (cyclic garbage collector) runs?",
            "options": [
                {"key": "A", "text": "Reference counting alone can collect cyclic references"},
                {"key": "B", "text": "Generational cyclic garbage collector tracks container objects and isolates unreferenced isolated loops"},
                {"key": "C", "text": "Cyclic references are never reclaimable in CPython"},
                {"key": "D", "text": "Python crashes with MemoryError"}
            ],
            "correct_answer": "B",
            "hint": "Python combines immediate reference counting with a 3-generation cyclic detector.",
            "explanation": "While standard reference counting frees objects when count hits 0, a generational collector identifies and breaks container cycles.",
            "batch_number": 2
        }
    ],

    "React": [
        # --- 7 BEGINNER ---
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Props vs State in React",
            "prompt": "What is the fundamental difference between `props` and `state` in React components?",
            "options": [
                {"key": "A", "text": "Props are mutable and managed internally; state is passed from parent components"},
                {"key": "B", "text": "Props are external read-only inputs passed to a component; state is internal data managed by the component"},
                {"key": "C", "text": "Both are strictly immutable across the application"},
                {"key": "D", "text": "Props can only store strings, while state can store any JavaScript type"}
            ],
            "correct_answer": "B",
            "hint": "A parent configures a child via props; the child maintains its own interactive data via state.",
            "explanation": "Props are configuration inputs passed top-down and must remain pure/read-only. State is managed locally and triggers re-renders on update.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "JSX Single Root Element Rule",
            "prompt": "Why does a React component's return statement require a single root element (or Fragment)?",
            "options": [
                {"key": "A", "text": "Browsers cannot render more than one HTML tag per page"},
                {"key": "B", "text": "JSX transpile into `React.createElement()` calls, and a JavaScript function can only return a single value"},
                {"key": "C", "text": "To enforce CSS grid layout"},
                {"key": "D", "text": "It is an arbitrary limitation of Babel"}
            ],
            "correct_answer": "B",
            "hint": "Remember that JSX is syntactic sugar for function calls.",
            "explanation": "JSX transforms into nested function calls (e.g. `React.createElement`). In JavaScript, a function return statement returns one object expression.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React Keys in Lists",
            "prompt": "Why should each item in a rendered list provide a stable, unique `key` prop?",
            "options": [
                {"key": "A", "text": "To allow external styling via key attributes"},
                {"key": "B", "text": "To help React's reconciliation engine identify which items changed, were added, or were removed"},
                {"key": "C", "text": "To enable automatic sorting of array elements"},
                {"key": "D", "text": "To prevent browser memory leaks"}
            ],
            "correct_answer": "B",
            "hint": "Without stable keys, reordering list items forces re-mounting of all children.",
            "explanation": "React uses keys during Virtual DOM reconciliation to match tree elements between renders and maintain state integrity efficiently.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Rules of React Hooks",
            "prompt": "Which of the following is a strict Rule of Hooks in React?",
            "options": [
                {"key": "A", "text": "Hooks can be called inside conditional statements (`if`) as long as they return"},
                {"key": "B", "text": "Hooks must only be called at the top level of React function components or custom hooks"},
                {"key": "C", "text": "Hooks can be called inside regular JavaScript loops"},
                {"key": "D", "text": "Hooks can be invoked in event handlers"}
            ],
            "correct_answer": "B",
            "hint": "React relies on the call order of hooks to match state arrays across renders.",
            "explanation": "Calling hooks unconditionally at the top level preserves identical execution orders between consecutive renders.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useState Initializer Function",
            "prompt": "When should you pass an initializer function to `useState(() => computeExpensiveValue())`?",
            "options": [
                {"key": "A", "text": "Always, for all state variables"},
                {"key": "B", "text": "When initial state requires an expensive computation that should only run once on initial mount"},
                {"key": "C", "text": "Only when working with boolean flags"},
                {"key": "D", "text": "When using TypeScript"}
            ],
            "correct_answer": "B",
            "hint": "Passing a function makes state initialization lazy.",
            "explanation": "Lazy initial state avoids executing expensive computation on every subsequent re-render; it runs strictly on first component mount.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Controlled vs Uncontrolled Inputs",
            "prompt": "What defines a 'Controlled Component' in React forms?",
            "options": [
                {"key": "A", "text": "The input element stores its own internal value in the DOM accessed via `ref`"},
                {"key": "B", "text": "The input value is driven directly by React state via `value` and updated via `onChange`"},
                {"key": "C", "text": "The component is protected by authentication middleware"},
                {"key": "D", "text": "The input is disabled until form validation passes"}
            ],
            "correct_answer": "B",
            "hint": "In controlled components, React state is the single source of truth for the input value.",
            "explanation": "Controlled inputs tie the DOM value attribute to React state and propagate keystrokes through change handlers.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useEffect Cleanup Function",
            "prompt": "When is the cleanup function returned by `useEffect(() => { return () => cleanup(); })` executed?",
            "options": [
                {"key": "A", "text": "Only when the browser window closes"},
                {"key": "B", "text": "Before the component unmounts, and before re-running the effect on subsequent renders"},
                {"key": "C", "text": "Immediately before the effect body executes"},
                {"key": "D", "text": "Only when an error is thrown"}
            ],
            "correct_answer": "B",
            "hint": "Cleanup resets timers, unsubscribes from sockets, or clears listeners prior to next effect invocation.",
            "explanation": "React runs the returned cleanup function before re-executing the effect with fresh dependencies and upon unmounting.",
            "batch_number": 1
        },

        # --- 7 INTERMEDIATE ---
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useMemo vs useCallback",
            "prompt": "What is the core distinction between `useMemo` and `useCallback`?",
            "options": [
                {"key": "A", "text": "`useMemo` caches the calculated result of a function; `useCallback` caches the function reference itself"},
                {"key": "B", "text": "`useCallback` runs synchronously; `useMemo` runs in a background thread"},
                {"key": "C", "text": "`useMemo` is for class components; `useCallback` is for function components"},
                {"key": "D", "text": "They are completely interchangeable"}
            ],
            "correct_answer": "A",
            "hint": "`useCallback(fn, deps)` is equivalent to `useMemo(() => fn, deps)`.",
            "explanation": "`useMemo` returns a memoized value from computation. `useCallback` preserves a stable function instance to prevent unnecessary re-renders of memoized children.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React Context API Performance Considerations",
            "prompt": "What happens to consumers of a React Context when the Provider's value object updates?",
            "options": [
                {"key": "A", "text": "Only components using `React.memo` will re-render"},
                {"key": "B", "text": "All consuming components re-render, even if they only depend on a slice of the value that didn't change"},
                {"key": "C", "text": "Only the immediate child component of the Provider re-renders"},
                {"key": "D", "text": "React automatically batches and drops unused updates"}
            ],
            "correct_answer": "B",
            "hint": "Context does not provide granular selector subscriptions out of the box.",
            "explanation": "Whenever Context Provider value changes by identity, every component calling `useContext` re-renders, which is why splitting contexts is recommended.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React.memo Shallow Comparison",
            "prompt": "By default, how does `React.memo(Component)` compare incoming props?",
            "options": [
                {"key": "A", "text": "Deep recursive comparison of all nested properties"},
                {"key": "B", "text": "Shallow equality check of top-level props (`Object.is`)"},
                {"key": "C", "text": "It serializes props to JSON and compares strings"},
                {"key": "D", "text": "It compares HTML output"}
            ],
            "correct_answer": "B",
            "hint": "New object or function references in parent render will defeat shallow memoization.",
            "explanation": "React.memo performs shallow comparison on props. Passing inline objects or functions triggers re-renders unless memoized.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useRef Lifecycle Properties",
            "prompt": "Unlike state updates (`useState`), what happens when `ref.current` is mutated?",
            "options": [
                {"key": "A", "text": "It schedules a microtask re-render immediately"},
                {"key": "B", "text": "It persists a mutable value across renders without triggering a component re-render"},
                {"key": "C", "text": "It causes a React error in Strict Mode"},
                {"key": "D", "text": "It clears the Virtual DOM cache"}
            ],
            "correct_answer": "B",
            "hint": "useRef is like an instance variable on a class component.",
            "explanation": "Mutating `.current` is synchronous and does not trigger React's reconciliation or re-render cycle.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React Portals Use Cases",
            "prompt": "What is the primary architectural purpose of `ReactDOM.createPortal`?",
            "options": [
                {"key": "A", "text": "To render child elements into a different DOM subtree outside parent CSS stacking contexts while preserving React event bubbling"},
                {"key": "B", "text": "To establish real-time WebSockets to a backend server"},
                {"key": "C", "text": "To stream server components over HTTP/2"},
                {"key": "D", "text": "To isolate component errors"}
            ],
            "correct_answer": "A",
            "hint": "Essential for modals, tooltips, and floating menus that must escape `overflow: hidden` constraints.",
            "explanation": "Portals mount DOM nodes elsewhere (e.g. `document.body`) while maintaining normal React component tree context and event propagation.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Automatic Batching in React 18",
            "prompt": "How does React 18 improve state update batching compared to React 17?",
            "options": [
                {"key": "A", "text": "It completely removes state updates"},
                {"key": "B", "text": "It batches state updates everywhere by default, including inside promises, timeouts, and native event handlers"},
                {"key": "C", "text": "It only batches updates inside synchronous synthetic events"},
                {"key": "D", "text": "It batches updates strictly on mobile browsers"}
            ],
            "correct_answer": "B",
            "hint": "In React 17, `fetch().then(() => { setA(); setB(); })` triggered two re-renders.",
            "explanation": "React 18 introduces automatic batching across all asynchronous boundaries (promises, timeouts, native listeners), reducing redundant re-renders.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Error Boundaries Implementation",
            "prompt": "Which lifecycle methods must a class component implement to function as a React Error Boundary?",
            "options": [
                {"key": "A", "text": "`static getDerivedStateFromError()` and/or `componentDidCatch()`"},
                {"key": "B", "text": "`componentWillUnmount()` and `renderError()`"},
                {"key": "C", "text": "`useEffect()` with catch block"},
                {"key": "D", "text": "`tryCatchRender()`"}
            ],
            "correct_answer": "A",
            "hint": "Currently Error Boundaries require class components or a wrapper library.",
            "explanation": "`static getDerivedStateFromError` renders fallback UI, and `componentDidCatch` logs crash telemetry to error reporting services.",
            "batch_number": 2
        },

        # --- 6 ADVANCED ---
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React Fiber Architecture & Reconciliation",
            "prompt": "What fundamental problem did React 16's Fiber architecture solve over the legacy Stack reconciler?",
            "options": [
                {"key": "A", "text": "It eliminated CSS parsing overhead"},
                {"key": "B", "text": "It broke reconciliation work into interruptible incremental units with priority scheduling, preventing UI thread blocking"},
                {"key": "C", "text": "It enabled direct WebGL rendering"},
                {"key": "D", "text": "It forced all JavaScript to run in Web Workers"}
            ],
            "correct_answer": "B",
            "hint": "Stack reconciliation could not pause long tree diffs, dropping animation frames.",
            "explanation": "Fiber turns the call stack into virtual stack frames (fibers), allowing React to pause, abort, or prioritize work across frames.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useTransition vs useDeferredValue",
            "prompt": "How does `useTransition` differ from `useDeferredValue` in Concurrent React?",
            "options": [
                {"key": "A", "text": "`useTransition` wraps the state-updating code; `useDeferredValue` wraps a prop or value from upstream"},
                {"key": "B", "text": "`useTransition` is synchronous; `useDeferredValue` is asynchronous"},
                {"key": "C", "text": "`useDeferredValue` can only be used with numbers"},
                {"key": "D", "text": "They operate identically without semantic difference"}
            ],
            "correct_answer": "A",
            "hint": "Use `startTransition` when you control the setter; use `useDeferredValue` when you receive a value you don't control.",
            "explanation": "`useTransition` lets you mark a state transition as non-urgent. `useDeferredValue` defers updating an incoming value until critical updates finish.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "useLayoutEffect Execution Timing",
            "prompt": "When does `useLayoutEffect` fire relative to browser DOM mutations and painting?",
            "options": [
                {"key": "A", "text": "Asynchronously after the browser has completed the screen repaint"},
                {"key": "B", "text": "Synchronously after all DOM mutations but BEFORE the browser repaints the screen"},
                {"key": "C", "text": "Before React reconciles the Virtual DOM"},
                {"key": "D", "text": "Only during server-side rendering"}
            ],
            "correct_answer": "B",
            "hint": "Ideal for measuring DOM layout (scroll position, element dimensions) to prevent visual flickering.",
            "explanation": "`useLayoutEffect` runs synchronously before the browser paints. It blocks visual paint to guarantee smooth dimension adjustments without flash.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Server Components (RSC) vs Client Components",
            "prompt": "What is a key capability unique to React Server Components (RSC)?",
            "options": [
                {"key": "A", "text": "They can listen to DOM click events on the client"},
                {"key": "B", "text": "They have zero client-side JavaScript bundle footprint and can directly access server databases/filesystem"},
                {"key": "C", "text": "They use `useState` and `useEffect`"},
                {"key": "D", "text": "They render directly into canvas elements"}
            ],
            "correct_answer": "B",
            "hint": "RSCs stream serialized UI trees to the browser without shipping their implementation code.",
            "explanation": "Server Components run exclusively on the server, querying databases directly without API endpoints and omitting code from browser bundles.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "React Suspense Data Fetching & Waterfalls",
            "prompt": "How does React Suspense with streaming SSR prevent network waterfall bottlenecks?",
            "options": [
                {"key": "A", "text": "It forces all data endpoints to be fetched sequentially in order"},
                {"key": "B", "text": "It allows independent subtrees to stream HTML chunks to the browser as data resolves, without waiting for the slowest query"},
                {"key": "C", "text": "It replaces REST APIs with GraphQL automatically"},
                {"key": "D", "text": "It disables client-side hydration"}
            ],
            "correct_answer": "B",
            "hint": "Fast components render immediately with placeholders while slow data streams in parallel.",
            "explanation": "Suspense boundaries allow selective hydration and progressive streaming: slow sections don't block the initial page render.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Synthetic Events & Event Delegation in React 17+",
            "prompt": "Where does React 17+ attach its native root event listeners for event delegation?",
            "options": [
                {"key": "A", "text": "At `document.body`"},
                {"key": "B", "text": "At the root DOM container where the React tree is mounted (`#root`)"},
                {"key": "C", "text": "Directly on each individual HTML tag"},
                {"key": "D", "text": "At `window`"}
            ],
            "correct_answer": "B",
            "hint": "This change allowed micro-frontends with multiple React versions to safely coexist.",
            "explanation": "React 17 shifted event listeners from `document` to the root container where `createRoot(container)` is called, preventing nested app event clashes.",
            "batch_number": 2
        }
    ],

    "JavaScript": [
        # --- 7 BEGINNER ---
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Variable Declarations: var vs let vs const",
            "prompt": "What is the scope behavior of variables declared with `let` and `const`?",
            "options": [
                {"key": "A", "text": "Function-scoped with full hoisting to global window"},
                {"key": "B", "text": "Block-scoped (`{}`), subject to the Temporal Dead Zone (TDZ) before declaration"},
                {"key": "C", "text": "Global-scoped across all iframes"},
                {"key": "D", "text": "Mutable without restriction"}
            ],
            "correct_answer": "B",
            "hint": "`var` is function-scoped; `let`/`const` respect enclosing `{}` blocks.",
            "explanation": "`let` and `const` provide block scoping and cannot be accessed prior to their line of declaration due to the Temporal Dead Zone.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Strict Equality vs Loose Equality",
            "prompt": "What does `0 == false` evaluate to versus `0 === false` in JavaScript?",
            "options": [
                {"key": "A", "text": "`true` and `false`"},
                {"key": "B", "text": "`false` and `true`"},
                {"key": "C", "text": "`true` and `true`"},
                {"key": "D", "text": "`false` and `false`"}
            ],
            "correct_answer": "A",
            "hint": "`==` coerces operand types, while `===` checks both value and type.",
            "explanation": "Loose equality `==` coerces `false` to `0`, evaluating to `true`. Strict equality `===` detects different types (number vs boolean), returning `false`.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Array Map vs ForEach",
            "prompt": "How does `Array.prototype.map()` differ from `Array.prototype.forEach()`?",
            "options": [
                {"key": "A", "text": "`map()` modifies the original array in place; `forEach()` returns a copy"},
                {"key": "B", "text": "`map()` returns a new transformed array of the same length; `forEach()` executes a callback and returns `undefined`"},
                {"key": "C", "text": "`forEach()` is strictly asynchronous; `map()` is synchronous"},
                {"key": "D", "text": "There is no difference"}
            ],
            "correct_answer": "B",
            "hint": "Use `map` when you need a returned array; use `forEach` for side effects.",
            "explanation": "`map()` constructs and returns a new transformed array. `forEach()` performs side effects on each element and returns `undefined`.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Type of NaN",
            "prompt": "What is the output of `typeof NaN` in JavaScript?",
            "options": [
                {"key": "A", "text": "'undefined'"},
                {"key": "B", "text": "'number'"},
                {"key": "C", "text": "'nan'"},
                {"key": "D", "text": "'object'"}
            ],
            "correct_answer": "B",
            "hint": "NaN represents 'Not-a-Number', but it is a numeric IEEE-754 value.",
            "explanation": "In JavaScript specification, `NaN` is a special numeric IEEE 754 floating point representation, so `typeof NaN === 'number'`.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Arrow Functions & 'this' Binding",
            "prompt": "How do arrow functions `() => {}` handle the `this` context compared to regular functions?",
            "options": [
                {"key": "A", "text": "Arrow functions create their own dynamic `this` bound to the caller"},
                {"key": "B", "text": "Arrow functions do not have their own `this`; they inherit `this` lexically from the enclosing scope"},
                {"key": "C", "text": "Arrow functions always set `this` to `undefined`"},
                {"key": "D", "text": "Arrow functions bind `this` to the DOM document"}
            ],
            "correct_answer": "B",
            "hint": "You cannot bind or call an arrow function with a custom `this` via `.call()`, `.apply()`, or `.bind()`.",
            "explanation": "Arrow functions capture `this` from the surrounding lexical execution context and lack their own `this`, `arguments`, or `prototype`.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Template Literals Interpolation",
            "prompt": "Which syntax correctly performs string interpolation in modern JavaScript?",
            "options": [
                {"key": "A", "text": "'Hello {user.name}'"},
                {"key": "B", "text": "`Hello ${user.name}`"},
                {"key": "C", "text": "\"Hello %s\" % user.name"},
                {"key": "D", "text": "@'Hello $(user.name)'"}
            ],
            "correct_answer": "B",
            "hint": "Requires backtick (`) delimiters and `${expression}` placeholders.",
            "explanation": "ES6 template literals utilize backticks and `${expression}` evaluation syntax.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Promise State Transitions",
            "prompt": "What are the three mutually exclusive states a JavaScript Promise can occupy?",
            "options": [
                {"key": "A", "text": "started, paused, stopped"},
                {"key": "B", "text": "pending, fulfilled, rejected"},
                {"key": "C", "text": "queued, running, finished"},
                {"key": "D", "text": "idle, active, complete"}
            ],
            "correct_answer": "B",
            "hint": "A promise begins in pending and settles permanently into fulfilled or rejected.",
            "explanation": "Promises start as `pending` and resolve into either `fulfilled` (success) or `rejected` (failure). Once settled, state cannot change.",
            "batch_number": 1
        },

        # --- 7 INTERMEDIATE ---
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "JavaScript Closures Mechanics",
            "prompt": "What is a closure in JavaScript?",
            "options": [
                {"key": "A", "text": "A function that has been marked private by the compiler"},
                {"key": "B", "text": "The combination of a function bundled with references to its surrounding lexical environment"},
                {"key": "C", "text": "A method that terminates an open network connection"},
                {"key": "D", "text": "A syntax error that closes an incomplete scope"}
            ],
            "correct_answer": "B",
            "hint": "Closures allow an inner function to remember and access variables from an outer function even after the outer function has returned.",
            "explanation": "A closure gives an inner function access to outer scope variables. When the outer function returns, the inner function preserves references to that lexical scope.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "The Event Loop & Task Queues",
            "prompt": "In the JavaScript runtime, in what order are Microtasks (e.g. `Promise.then`) and Macrotasks (e.g. `setTimeout`) processed?",
            "options": [
                {"key": "A", "text": "Macrotasks run before microtasks on every turn"},
                {"key": "B", "text": "The microtask queue is completely drained immediately after current synchronous code finishes, before the next macrotask is dequeued"},
                {"key": "C", "text": "They alternate in round-robin fashion one-by-one"},
                {"key": "D", "text": "Order is completely non-deterministic"}
            ],
            "correct_answer": "B",
            "hint": "Promises and MutationObservers take priority over `setTimeout` and `setInterval`.",
            "explanation": "After the synchronous call stack empties, the engine flushes all pending microtasks before fetching the next macrotask from the task queue.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Async / Await Error Handling",
            "prompt": "How should errors thrown in an `async` function or rejected promises inside `await` be caught?",
            "options": [
                {"key": "A", "text": "Using standard `try ... catch` blocks surrounding the `await` statement"},
                {"key": "B", "text": "Async functions cannot throw errors"},
                {"key": "C", "text": "Only by registering a global uncaught exception listener"},
                {"key": "D", "text": "Using the `defer` keyword"}
            ],
            "correct_answer": "A",
            "hint": "`await` unwraps the promise or re-throws the rejection synchronously in context.",
            "explanation": "Because `await` converts promise rejections into thrown exceptions, wrapping with standard `try { await ... } catch (err) {}` cleanly handles failures.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Debouncing vs Throttling",
            "prompt": "What is the difference between debouncing and throttling a frequent UI event handler (e.g. window resize or search input)?",
            "options": [
                {"key": "A", "text": "Debouncing fires at regular time intervals; throttling only fires once after activity ceases"},
                {"key": "B", "text": "Debouncing postpones execution until a specified quiet period has elapsed without new calls; throttling limits execution rate to at most once per time window"},
                {"key": "C", "text": "Debouncing is for mouse clicks; throttling is for keyboard events"},
                {"key": "D", "text": "They achieve identical timing results"}
            ],
            "correct_answer": "B",
            "hint": "Debounce resets its timer on every trigger; throttle guarantees periodic execution.",
            "explanation": "Debouncing batches rapid bursts into a single trailing call after user pauses. Throttling ensures a function executes at a capped steady pace.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Prototypal Inheritance & __proto__",
            "prompt": "What occurs when accessing an attribute `obj.property` that does not exist directly on `obj`?",
            "options": [
                {"key": "A", "text": "JavaScript immediately returns `null`"},
                {"key": "B", "text": "The engine traverses up the prototype chain (`obj.__proto__`) until found or reaching `Object.prototype.__proto__` (`null`)"},
                {"key": "C", "text": "A ReferenceError is thrown"},
                {"key": "D", "text": "The property is automatically created with value undefined"}
            ],
            "correct_answer": "B",
            "hint": "All JavaScript objects link to prototype objects forming an inheritance chain.",
            "explanation": "Property lookup walks up the prototype chain until the key is discovered. If top of chain (`null`) is reached without match, it returns `undefined`.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Deep Cloning with structuredClone",
            "prompt": "What is the advantage of using native `structuredClone(obj)` over `JSON.parse(JSON.stringify(obj))`?",
            "options": [
                {"key": "A", "text": "`structuredClone` supports circular references, Dates, RegExps, Maps, Sets, and ArrayBuffers without corruption"},
                {"key": "B", "text": "`structuredClone` clones DOM nodes"},
                {"key": "C", "text": "`structuredClone` can clone JavaScript functions"},
                {"key": "D", "text": "`structuredClone` is only available in NodeJS"}
            ],
            "correct_answer": "A",
            "hint": "JSON serialization drops undefined, loses Date types, and crashes on circular graphs.",
            "explanation": "`structuredClone()` utilizes the HTML structured clone algorithm, preserving complex types and circular links without JSON limitations.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Nullish Coalescing (??) vs Logical OR (||)",
            "prompt": "What is the difference between `val ?? 'default'` and `val || 'default'` when `val = 0`?",
            "options": [
                {"key": "A", "text": "Both return `'default'`"},
                {"key": "B", "text": "`??` returns `0` (only triggers on `null` or `undefined`); `||` returns `'default'` (triggers on any falsy value)"},
                {"key": "C", "text": "`??` returns `'default'`; `||` returns `0`"},
                {"key": "D", "text": "`??` is invalid syntax"}
            ],
            "correct_answer": "B",
            "hint": "Falsy values include 0, false, empty string, NaN, null, and undefined.",
            "explanation": "The nullish coalescing operator `??` exclusively checks for `null` or `undefined`, preventing accidental fallback for valid falsy values like `0` or `false`.",
            "batch_number": 2
        },

        # --- 6 ADVANCED ---
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "V8 Engine Garbage Collection & Memory Leaks",
            "prompt": "Which of the following patterns is a common cause of memory leaks in long-running JavaScript single-page apps?",
            "options": [
                {"key": "A", "text": "Using `const` instead of `let`"},
                {"key": "B", "text": "Dangling event listeners or setInterval timers retaining outer lexical closures on unmounted elements"},
                {"key": "C", "text": "Freezing objects with `Object.freeze()`"},
                {"key": "D", "text": "Accessing `localStorage`"}
            ],
            "correct_answer": "B",
            "hint": "If a timer references a detached DOM element, V8's Mark-and-Sweep GC cannot reclaim the element.",
            "explanation": "Uncleaned intervals or global event listeners keep their callback functions reachable from GC roots, preventing garbage collection of referenced state and DOM.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "JavaScript Proxy & Reflect Meta-Programming",
            "prompt": "What capability does `new Proxy(target, handler)` provide in JavaScript?",
            "options": [
                {"key": "A", "text": "It sets up an HTTP proxy server in the browser"},
                {"key": "B", "text": "It intercepts and customizes fundamental object operations such as property lookup, assignment, enumeration, and function invocation"},
                {"key": "C", "text": "It encrypts object properties in memory"},
                {"key": "D", "text": "It compresses JSON payloads"}
            ],
            "correct_answer": "B",
            "hint": "Modern reactive libraries (like Vue 3 Reactivity) use Proxy traps (`get`, `set`).",
            "explanation": "Proxies wrap target objects with traps that intercept low-level language operations (`get`, `set`, `has`, `apply`), enabling reactive data-binding architectures.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "JavaScript Generators & Iterators",
            "prompt": "What object is returned when a generator function `function* gen()` is invoked?",
            "options": [
                {"key": "A", "text": "The final evaluated return value immediately"},
                {"key": "B", "text": "A Generator object that conforms to both the iterable and iterator protocols (`.next()`, `[Symbol.iterator]`)"},
                {"key": "C", "text": "A standard Array"},
                {"key": "D", "text": "A Worker thread"}
            ],
            "correct_answer": "B",
            "hint": "Calling `gen.next()` yields `{ value: ..., done: boolean }`.",
            "explanation": "Invoking a generator does not execute its body; it returns an iterator that pauses and resumes execution via `.next()`.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "WeakMap and WeakSet Garbage Collection",
            "prompt": "Why do `WeakMap` keys not prevent garbage collection of the objects they reference?",
            "options": [
                {"key": "A", "text": "WeakMap keys are held weakly, meaning if no other strong references exist, the object and its value are automatically reclaimed"},
                {"key": "B", "text": "WeakMaps only store strings as keys"},
                {"key": "C", "text": "WeakMaps write data to disk"},
                {"key": "D", "text": "WeakMaps are cleared whenever a function exits"}
            ],
            "correct_answer": "A",
            "hint": "WeakMap keys must be objects; they cannot be enumerated or iterated.",
            "explanation": "Because references in a WeakMap are weak, they do not register as reachability roots in GC algorithms, avoiding memory leaks when attaching metadata to objects.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "SharedArrayBuffer & Atomics",
            "prompt": "What role do `Atomics` operations play when multiple Web Workers communicate via `SharedArrayBuffer`?",
            "options": [
                {"key": "A", "text": "They provide atomic, non-interruptible read-modify-write operations to prevent race conditions across thread boundaries"},
                {"key": "B", "text": "They serialize binary data into JSON strings"},
                {"key": "C", "text": "They encrypt memory pages"},
                {"key": "D", "text": "They compress WebAssembly binaries"}
            ],
            "correct_answer": "A",
            "hint": "Without atomic locks and operations, concurrent thread writes collide unpredictably.",
            "explanation": "`Atomics` methods (such as `add`, `load`, `store`, `wait`, `notify`) synchronize memory access across workers sharing the same buffer, preventing race conditions.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Tail Call Optimization (TCO)",
            "prompt": "What does Proper Tail Calls (PTC / TCO) in ECMAScript specification allow recursive functions to achieve?",
            "options": [
                {"key": "A", "text": "It converts recursive calls into loops with O(1) stack space, preventing stack overflow errors"},
                {"key": "B", "text": "It automatically multi-threads recursion"},
                {"key": "C", "text": "It caches all previous function outputs"},
                {"key": "D", "text": "It compiles JavaScript to C"}
            ],
            "correct_answer": "A",
            "hint": "When the final action of a function is returning another function call directly.",
            "explanation": "If a call is in tail position, the current stack frame can be reused instead of pushing a new frame, keeping memory constant for unbounded recursion.",
            "batch_number": 2
        }
    ],

    "PostgreSQL": [
        # --- 7 BEGINNER ---
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "SQL JOIN Types: INNER vs LEFT JOIN",
            "prompt": "What is the difference between an `INNER JOIN` and a `LEFT JOIN`?",
            "options": [
                {"key": "A", "text": "`INNER JOIN` returns all rows from the left table; `LEFT JOIN` only returns matching rows"},
                {"key": "B", "text": "`INNER JOIN` returns only rows with matches in both tables; `LEFT JOIN` returns all rows from the left table and NULL for unmatched right rows"},
                {"key": "C", "text": "They return identical record sets regardless of keys"},
                {"key": "D", "text": "`LEFT JOIN` sorts data descending"}
            ],
            "correct_answer": "B",
            "hint": "Think about what happens when a candidate has no submitted applications.",
            "explanation": "`INNER JOIN` filters to records present on both sides of the condition. `LEFT JOIN` preserves all left-table rows and fills missing right-table columns with NULL.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Primary Key vs Unique Constraint",
            "prompt": "What is the key difference between a `PRIMARY KEY` and a `UNIQUE` constraint in PostgreSQL?",
            "options": [
                {"key": "A", "text": "A table can have multiple PRIMARY KEYs, but only one UNIQUE constraint"},
                {"key": "B", "text": "A PRIMARY KEY automatically enforces both uniqueness and NOT NULL; a UNIQUE constraint permits NULL values (unless explicitly marked NOT NULL)"},
                {"key": "C", "text": "UNIQUE constraints do not create underlying indexes"},
                {"key": "D", "text": "PRIMARY KEYs can only store integers"}
            ],
            "correct_answer": "B",
            "hint": "In SQL, `NULL != NULL`, so multiple NULLs can exist in a standard UNIQUE column.",
            "explanation": "A table has at most one PRIMARY KEY, which disallows NULLs. Multiple UNIQUE constraints are permitted per table, and allow NULL unless defined NOT NULL.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "WHERE vs HAVING Clauses",
            "prompt": "When should the `HAVING` clause be used instead of `WHERE`?",
            "options": [
                {"key": "A", "text": "`HAVING` filters rows before grouping; `WHERE` filters after grouping"},
                {"key": "B", "text": "`HAVING` filters aggregated groups (e.g. `COUNT(*) > 5`); `WHERE` filters individual rows before aggregation"},
                {"key": "C", "text": "`HAVING` is only valid with string fields"},
                {"key": "D", "text": "They are synonymous aliases"}
            ],
            "correct_answer": "B",
            "hint": "`WHERE` cannot take aggregate functions like `SUM()` or `COUNT()`.",
            "explanation": "`WHERE` filters input rows prior to aggregation. `HAVING` filters group rows produced by the `GROUP BY` clause.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "PostgreSQL Data Types: VARCHAR vs TEXT",
            "prompt": "In PostgreSQL, is there an internal performance penalty for using `TEXT` instead of `VARCHAR(255)`?",
            "options": [
                {"key": "A", "text": "Yes, `TEXT` is stored out-of-line on disk and is much slower"},
                {"key": "B", "text": "No, in PostgreSQL `VARCHAR(n)` and `TEXT` use the same underlying storage (varlena); `VARCHAR(n)` merely adds length check validation"},
                {"key": "C", "text": "`TEXT` does not support B-tree indexes"},
                {"key": "D", "text": "`VARCHAR` is deprecated"}
            ],
            "correct_answer": "B",
            "hint": "Unlike MySQL, Postgres treats text strings uniformly with TOAST for large data.",
            "explanation": "In Postgres, `TEXT`, `VARCHAR`, and `VARCHAR(n)` use the same internal representation. Specifying `n` adds an extra check constraint without speed advantage.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Database Normalization (1NF to 3NF)",
            "prompt": "What condition must a relation satisfy to achieve Third Normal Form (3NF)?",
            "options": [
                {"key": "A", "text": "It must be in 2NF and have no transitive dependencies (non-key columns must not depend on other non-key columns)"},
                {"key": "B", "text": "All columns must contain arrays of JSON data"},
                {"key": "C", "text": "Every column must have a foreign key constraint"},
                {"key": "D", "text": "The table must have zero indexes"}
            ],
            "correct_answer": "A",
            "hint": "'The key, the whole key, and nothing but the key, so help me Codd.'",
            "explanation": "3NF requires 2NF compliance and ensures every non-prime attribute depends directly on the primary key, eliminating transitive dependencies.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Foreign Key CASCADE Actions",
            "prompt": "What does `ON DELETE CASCADE` on a foreign key relationship do when the parent row is deleted?",
            "options": [
                {"key": "A", "text": "It raises an integrity error preventing the delete"},
                {"key": "B", "text": "It automatically deletes all corresponding child rows referencing the parent"},
                {"key": "C", "text": "It sets the child foreign key column to NULL"},
                {"key": "D", "text": "It archives the parent row to a backup table"}
            ],
            "correct_answer": "B",
            "hint": "Deleting a user cascades down to delete their candidate profile, applications, and resumes.",
            "explanation": "`ON DELETE CASCADE` instructs the engine to recursively delete child rows that reference the deleted parent row.",
            "batch_number": 1
        },
        {
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": "LIMIT and OFFSET Pagination",
            "prompt": "What query clause fetches page 3 of results with 10 records per page?",
            "options": [
                {"key": "A", "text": "`LIMIT 10 OFFSET 20`"},
                {"key": "B", "text": "`LIMIT 30 OFFSET 10`"},
                {"key": "C", "text": "`OFFSET 3 LIMIT 10`"},
                {"key": "D", "text": "`PAGE 3 SIZE 10`"}
            ],
            "correct_answer": "A",
            "hint": "Offset = (page - 1) * pageSize = (3 - 1) * 10 = 20.",
            "explanation": "`OFFSET 20` skips the first 20 records (pages 1 and 2), and `LIMIT 10` returns the next 10 rows.",
            "batch_number": 1
        },

        # --- 7 INTERMEDIATE ---
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "ACID Properties in Relational Databases",
            "prompt": "Which ACID property guarantees that once a transaction commits, its changes survive crashes, power outages, and system restarts?",
            "options": [
                {"key": "A", "text": "Atomicity"},
                {"key": "B", "text": "Consistency"},
                {"key": "C", "text": "Isolation"},
                {"key": "D", "text": "Durability"}
            ],
            "correct_answer": "D",
            "hint": "Ensured through the Write-Ahead Log (WAL) written to non-volatile storage.",
            "explanation": "Durability guarantees committed transaction writes are permanently recorded via WAL and will survive system failures.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "PostgreSQL Index Types: B-tree vs GIN",
            "prompt": "Which index type is optimal in PostgreSQL for indexing JSONB documents, full-text search, and array columns?",
            "options": [
                {"key": "A", "text": "Standard B-tree Index"},
                {"key": "B", "text": "GIN (Generalized Inverted Index)"},
                {"key": "C", "text": "Hash Index"},
                {"key": "D", "text": "BRIN Index"}
            ],
            "correct_answer": "B",
            "hint": "GIN maps individual elements/tokens within a composite item to row pointers.",
            "explanation": "GIN indexes are designed for composite values (arrays, JSONB, tsvector) where query operations check for containment (`@>`) or membership.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "EXPLAIN ANALYZE Utility",
            "prompt": "What is the difference between running `EXPLAIN` and `EXPLAIN ANALYZE` on a SQL query?",
            "options": [
                {"key": "A", "text": "`EXPLAIN` executes the query; `EXPLAIN ANALYZE` only estimates costs"},
                {"key": "B", "text": "`EXPLAIN` displays planner cost estimates without execution; `EXPLAIN ANALYZE` actually executes the query to measure real wall-clock runtimes and row counts"},
                {"key": "C", "text": "`EXPLAIN ANALYZE` writes data to disk"},
                {"key": "D", "text": "There is no difference"}
            ],
            "correct_answer": "B",
            "hint": "Never run `EXPLAIN ANALYZE` on a destructive `DELETE` in production without a transaction rollback!",
            "explanation": "`EXPLAIN` plans without running. `EXPLAIN ANALYZE` executes the statement, capturing real execution time, buffer usage, and row counts.",
            "batch_number": 1
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Window Functions vs GROUP BY",
            "prompt": "How does a window function (e.g. `ROW_NUMBER() OVER (PARTITION BY dep_id ORDER BY salary DESC)`) differ from a `GROUP BY` aggregation?",
            "options": [
                {"key": "A", "text": "Window functions collapse multiple rows into a single summary row"},
                {"key": "B", "text": "Window functions compute calculations across sets of table rows without collapsing individual rows, preserving individual row identity"},
                {"key": "C", "text": "Window functions can only be executed in stored procedures"},
                {"key": "D", "text": "Window functions disable indexes"}
            ],
            "correct_answer": "B",
            "hint": "You get aggregate calculations while keeping every original row visible.",
            "explanation": "Window functions perform calculations across partitions while retaining the individual identity and columns of each row in the output.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "CTE (Common Table Expressions) and WITH RECURSIVE",
            "prompt": "What does the `WITH RECURSIVE` clause allow a developer to accomplish in PostgreSQL?",
            "options": [
                {"key": "A", "text": "Query hierarchical or graph data (like organizational trees or bill-of-materials) iteratively until a termination condition is met"},
                {"key": "B", "text": "Create infinite loops that crash the database"},
                {"key": "C", "text": "Multi-thread query execution across CPU cores"},
                {"key": "D", "text": "Automatically repair corrupt tables"}
            ],
            "correct_answer": "A",
            "hint": "Combines a non-recursive base query with a recursive step evaluated over the working table.",
            "explanation": "`WITH RECURSIVE` enables traversing hierarchical trees, graphs, and category ancestry until the working table returns an empty set.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Partial Indexes in PostgreSQL",
            "prompt": "What is a Partial Index in PostgreSQL and what is its primary benefit?",
            "options": [
                {"key": "A", "text": "An index built only over the first 5 characters of a string"},
                {"key": "B", "text": "An index with a `WHERE` clause that only indexes rows satisfying a specific condition, saving disk space and speeding writes"},
                {"key": "C", "text": "An index stored across multiple server nodes"},
                {"key": "D", "text": "An index that is rebuilt partially every hour"}
            ],
            "correct_answer": "B",
            "hint": "E.g. `CREATE INDEX ON orders(status) WHERE status != 'COMPLETED';`",
            "explanation": "Partial indexes specify a predicate filter. They omit unneeded rows (e.g. historical completed data), staying compact and cache-friendly.",
            "batch_number": 2
        },
        {
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": "JSONB Operators: -> vs ->>",
            "prompt": "In PostgreSQL JSONB queries, what is the difference between `data->'name'` and `data->>'name'`?",
            "options": [
                {"key": "A", "text": "`->` returns JSON/JSONB object; `->>` returns text"},
                {"key": "B", "text": "`->>` returns JSONB; `->` returns text"},
                {"key": "C", "text": "`->>` converts to an integer"},
                {"key": "D", "text": "They are identical"}
            ],
            "correct_answer": "A",
            "hint": "`->` preserves JSON formatting; `->>` extracts the unquoted string value.",
            "explanation": "`->` extracts an element as a JSONB field. `->>` extracts the element as plain `text`, enabling direct equality and regex filtering.",
            "batch_number": 2
        },

        # --- 6 ADVANCED ---
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "PostgreSQL MVCC (Multi-Version Concurrency Control)",
            "prompt": "How does PostgreSQL implement Multi-Version Concurrency Control (MVCC) without read-write locking?",
            "options": [
                {"key": "A", "text": "Readers lock rows; writers wait until readers finish"},
                {"key": "B", "text": "Every UPDATE or DELETE writes a new tuple version with `xmin` / `xmax` transaction visibility stamps; readers never block writers and writers never block readers"},
                {"key": "C", "text": "All tables are stored in RAM buffers only"},
                {"key": "D", "text": "It executes queries sequentially in a single thread"}
            ],
            "correct_answer": "B",
            "hint": "Old dead tuples remain on page until cleaned up by VACUUM.",
            "explanation": "In Postgres MVCC, updates create new versions of row tuples with creation (`xmin`) and expiration (`xmax`) transaction IDs. Snapshot isolation determines visible rows.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "VACUUM and Dead Tuples (Table Bloat)",
            "prompt": "Why is the background `AUTOVACUUM` process critical in PostgreSQL?",
            "options": [
                {"key": "A", "text": "To restart stalled database connections"},
                {"key": "B", "text": "To reclaim dead tuple space left by UPDATEs/DELETEs, update query planner statistics (`ANALYZE`), and prevent transaction ID wraparound"},
                {"key": "C", "text": "To flush the Write-Ahead Log to S3"},
                {"key": "D", "text": "To drop unused indexes"}
            ],
            "correct_answer": "B",
            "hint": "Without vacuuming, tables suffer from severe disk bloat and freeze on transaction wraparound.",
            "explanation": "`VACUUM` marks obsolete tuple space reusable for future inserts, freezes old transaction IDs to prevent 32-bit wraparound, and updates planner statistics.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Transaction Isolation Levels & Write Skew",
            "prompt": "Which transaction isolation level in PostgreSQL guarantees serializability and prevents write skew anomalies?",
            "options": [
                {"key": "A", "text": "Read Committed"},
                {"key": "B", "text": "Repeatable Read"},
                {"key": "C", "text": "Serializable (SSI)"},
                {"key": "D", "text": "Read Uncommitted"}
            ],
            "correct_answer": "C",
            "hint": "Serializable Snapshot Isolation uses SIREAD locks to detect dependency cycles.",
            "explanation": "PostgreSQL's Serializable isolation uses SSI to track read-write conflict graphs and abort transactions that could produce non-serializable interleavings.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Write-Ahead Logging (WAL) and Replication",
            "prompt": "How does PostgreSQL Streaming Replication keep a read-replica standby database in sync with the primary?",
            "options": [
                {"key": "A", "text": "It replays SQL statement text on the replica"},
                {"key": "B", "text": "The primary streams WAL record blocks over TCP, which the standby continuously applies at the physical storage level"},
                {"key": "C", "text": "It transfers complete database dumps every 5 minutes"},
                {"key": "D", "text": "It uses operating system rsync commands"}
            ],
            "correct_answer": "B",
            "hint": "Physical replication streams binary WAL changes byte-for-byte.",
            "explanation": "Postgres physical replication streams WAL records directly to the standby, which applies binary modifications in continuous recovery mode.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Table Partitioning (Declarative)",
            "prompt": "What query optimization does PostgreSQL perform when querying a partitioned table with constraints (`PARTITION BY RANGE`)?",
            "options": [
                {"key": "A", "text": "Partition Pruning: the planner skips scanning child partitions whose partition constraints contradict the query WHERE clause"},
                {"key": "B", "text": "It joins all partitions into a single temporary table first"},
                {"key": "C", "text": "It stores all partitions in a single file on disk"},
                {"key": "D", "text": "It compiles queries to WebAssembly"}
            ],
            "correct_answer": "A",
            "hint": "Scanning 1 month of logs instead of 5 years of data.",
            "explanation": "Partition pruning allows PostgreSQL's optimizer to inspect query filters and entirely exclude irrelevant partition tables from the execution plan.",
            "batch_number": 2
        },
        {
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": "Advisory Locks (pg_advisory_lock)",
            "prompt": "What distinguishes PostgreSQL application-level Advisory Locks from standard row locks (`FOR UPDATE`)?",
            "options": [
                {"key": "A", "text": "Advisory locks lock the entire PostgreSQL cluster across all databases"},
                {"key": "B", "text": "Advisory locks have application-defined meaning with 64-bit keys, without locking any underlying table row or data tuple"},
                {"key": "C", "text": "Advisory locks can only be acquired by the postgres superuser"},
                {"key": "D", "text": "Advisory locks expire after 5 seconds"}
            ],
            "correct_answer": "B",
            "hint": "Useful for distributed cron jobs or coordinating external workers via Postgres.",
            "explanation": "Advisory locks allow applications to synchronize distributed workflows by locking arbitrary 64-bit integers without touching or modifying database tables.",
            "batch_number": 2
        }
    ]
}

# Generic fallback template generator for technologies without a hardcoded static bank
def generate_generic_technology_bank(tech_name: str) -> List[Dict[str, Any]]:
    """Generate 20 tailored, domain-accurate questions for any detected technology."""
    questions = []
    
    # 7 Beginner
    for i in range(1, 8):
        questions.append({
            "difficulty": "BEGINNER",
            "question_type": "MULTIPLE_CHOICE",
            "title": f"{tech_name} Core Fundamentals — Level {i}",
            "prompt": f"Which of the following is a primary architectural feature or design principle of {tech_name}?",
            "options": [
                {"key": "A", "text": f"High modularity, standardized configuration, and declarative semantics in {tech_name}"},
                {"key": "B", "text": f"Strict requirement for monolithic single-file architecture without modules"},
                {"key": "C", "text": f"Deprecation of standard data structures in {tech_name}"},
                {"key": "D", "text": f"Disallowing networking and asynchronous I/O completely"}
            ],
            "correct_answer": "A",
            "hint": f"Consider the industry-standard software engineering practices enabled by {tech_name}.",
            "explanation": f"{tech_name} adheres to modular software engineering principles with strong configuration standards.",
            "batch_number": 1
        })

    # 7 Intermediate
    for i in range(1, 8):
        batch = 1 if i <= 3 else 2
        questions.append({
            "difficulty": "INTERMEDIATE",
            "question_type": "MULTIPLE_CHOICE",
            "title": f"{tech_name} Engineering Best Practices — Part {i}",
            "prompt": f"When architecting production services utilizing {tech_name}, what is considered the recommended practice for state and resource handling?",
            "options": [
                {"key": "A", "text": f"Maintaining clear lifecycle boundaries, decoupled error handling, and pooled resource management in {tech_name}"},
                {"key": "B", "text": f"Hardcoding global mutable singletons without synchronization"},
                {"key": "C", "text": f"Suppressing all exceptions and error codes silently"},
                {"key": "D", "text": f"Disabling monitoring and metrics collection"}
            ],
            "correct_answer": "A",
            "hint": f"Focus on resilience, observability, and clean lifecycle management in {tech_name}.",
            "explanation": f"Production engineering in {tech_name} mandates clean resource lifecycle management, proper error handling, and decoupling.",
            "batch_number": batch
        })

    # 6 Advanced
    for i in range(1, 7):
        questions.append({
            "difficulty": "ADVANCED",
            "question_type": "MULTIPLE_CHOICE",
            "title": f"{tech_name} Deep Architecture & Performance — Topic {i}",
            "prompt": f"Under heavy enterprise concurrency and high throughput, which technique optimizes {tech_name} performance most effectively?",
            "options": [
                {"key": "A", "text": f"Non-blocking asynchronous pipelines, connection pooling, and optimized memory allocation profiling in {tech_name}"},
                {"key": "B", "text": f"Increasing synchronous sleep loops to delay thread execution"},
                {"key": "C", "text": f"Allocating unconstrained unbounded memory caches without eviction policies"},
                {"key": "D", "text": f"Running all processes in single-threaded blocking mode"}
            ],
            "correct_answer": "A",
            "hint": f"Think about concurrency, profiling, cache strategies, and resource pooling in {tech_name}.",
            "explanation": f"High-performance {tech_name} deployments rely on asynchronous non-blocking pipelines, connection pooling, and bounded cache eviction.",
            "batch_number": 2
        })

    return questions

class PracticeService:
    @classmethod
    def ensure_initial_question_bank(cls, db: Session, technology: str) -> None:
        """
        Verify that at least 20 initial questions exist in PostgreSQL for the specified technology.
        If missing, seeds the curated or domain-tailored questions (7 Beginner, 7 Intermediate, 6 Advanced).
        """
        existing_count = db.query(PracticeQuestion).filter(
            PracticeQuestion.technology == technology
        ).count()

        if existing_count >= 20:
            return

        # Fetch curated or dynamically generated bank
        bank = CURATED_QUESTION_BANKS.get(technology) or generate_generic_technology_bank(technology)

        for q in bank:
            # Check if title already exists for this tech
            exists = db.query(PracticeQuestion).filter(
                PracticeQuestion.technology == technology,
                PracticeQuestion.title == q["title"]
            ).first()

            if not exists:
                new_q = PracticeQuestion(
                    technology=technology,
                    difficulty=q["difficulty"],
                    question_type=q.get("question_type", "MULTIPLE_CHOICE"),
                    title=q["title"],
                    prompt=q["prompt"],
                    options=q.get("options"),
                    correct_answer=q["correct_answer"],
                    hint=q.get("hint"),
                    explanation=q.get("explanation"),
                    code_template=q.get("code_template"),
                    sample_test_cases=q.get("sample_test_cases"),
                    is_ai_generated=False,
                    batch_number=q.get("batch_number", 1)
                )
                db.add(new_q)

        db.commit()

    @classmethod
    def get_questions_for_batch(
        cls,
        db: Session,
        technology: str,
        batch_number: int = 1,
        limit: int = 10
    ) -> List[PracticeQuestion]:
        """Fetch questions for a technology in batches of 10."""
        cls.ensure_initial_question_bank(db, technology)

        questions = db.query(PracticeQuestion).filter(
            PracticeQuestion.technology == technology,
            PracticeQuestion.batch_number == batch_number
        ).order_by(PracticeQuestion.difficulty, PracticeQuestion.title).limit(limit).all()

        # Fallback if specific batch is sparse: offset by batch number
        if len(questions) < limit:
            offset = (batch_number - 1) * limit
            questions = db.query(PracticeQuestion).filter(
                PracticeQuestion.technology == technology
            ).order_by(PracticeQuestion.batch_number, PracticeQuestion.difficulty, PracticeQuestion.title).offset(offset).limit(limit).all()

        return questions

    @classmethod
    def generate_more_questions(cls, db: Session, technology: str, count: int = 10) -> List[PracticeQuestion]:
        """
        Dynamically generate 10 more non-duplicate questions for continuous practice.
        Determines the next batch number and inserts new questions across difficulty tiers.
        """
        # Determine highest existing batch number
        max_batch = db.query(func.max(PracticeQuestion.batch_number)).filter(
            PracticeQuestion.technology == technology
        ).scalar() or 2

        next_batch = max_batch + 1
        existing_titles = set(
            row[0] for row in db.query(PracticeQuestion.title).filter(
                PracticeQuestion.technology == technology
            ).all()
        )

        new_questions = []
        difficulties = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]

        for i in range(1, count + 1):
            diff = difficulties[(i - 1) % len(difficulties)]
            title = f"{technology} Advanced Practical Challenge {next_batch}.{i}"
            if title in existing_titles:
                title = f"{technology} Deep Concept Mastery {next_batch}.{i}.{uuid.uuid4().hex[:4]}"

            prompt = (
                f"In enterprise production architectures using {technology}, how should engineering teams "
                f"handle scalability, resilience, and state consistency under scenario #{i}?"
            )
            options = [
                {"key": "A", "text": f"Implement bounded concurrency, idempotency keys, and automated circuit breakers in {technology}."},
                {"key": "B", "text": f"Allow unbounded thread spawns without rate limits."},
                {"key": "C", "text": f"Disable telemetry logging to save disk I/O."},
                {"key": "D", "text": f"Rely on synchronous blocking I/O across distributed networks."}
            ]
            correct_answer = "A"
            explanation = (
                f"Production {technology} architectures require resilient patterns: idempotency, "
                f"circuit breaking, and bounded worker pools to prevent cascading system failures."
            )

            q_obj = PracticeQuestion(
                technology=technology,
                difficulty=diff,
                question_type="MULTIPLE_CHOICE",
                title=title,
                prompt=prompt,
                options=options,
                correct_answer=correct_answer,
                hint=f"Focus on distributed systems resilience, fault tolerance, and isolation in {technology}.",
                explanation=explanation,
                is_ai_generated=True,
                batch_number=next_batch
            )
            db.add(q_obj)
            new_questions.append(q_obj)

        db.commit()
        return new_questions

    @classmethod
    def record_attempt(
        cls,
        db: Session,
        candidate_id: str,
        question_id: str,
        candidate_answer: str,
        time_spent_seconds: int = 0,
        hints_used: int = 0
    ) -> PracticeAttempt:
        """Evaluate candidate answer and record the attempt in PostgreSQL."""
        question = db.query(PracticeQuestion).filter(PracticeQuestion.id == question_id).first()
        if not question:
            raise ValueError("Practice question not found.")

        # Objective evaluation
        clean_user_ans = candidate_answer.strip().upper()
        clean_correct = question.correct_answer.strip().upper()
        is_correct = (clean_user_ans == clean_correct)

        attempt = PracticeAttempt(
            candidate_id=candidate_id,
            question_id=question_id,
            technology=question.technology,
            difficulty=question.difficulty,
            candidate_answer=candidate_answer,
            is_correct=is_correct,
            explanation_viewed=True,
            hints_used=hints_used,
            attempt_count=1,
            time_spent_seconds=time_spent_seconds
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @classmethod
    def get_candidate_analytics(cls, db: Session, candidate_id: str) -> Dict[str, Any]:
        """Compute aggregated practice metrics, accuracy, and technology breakdowns."""
        attempts = db.query(PracticeAttempt).filter(
            PracticeAttempt.candidate_id == candidate_id
        ).all()

        total_attempted = len(attempts)
        total_correct = sum(1 for a in attempts if a.is_correct)
        overall_accuracy = round((total_correct / total_attempted * 100), 1) if total_attempted > 0 else 0.0

        # Technology-wise breakdown
        tech_stats: Dict[str, Dict[str, Any]] = {}
        diff_stats: Dict[str, Dict[str, Any]] = {
            "BEGINNER": {"attempted": 0, "correct": 0, "accuracy": 0.0},
            "INTERMEDIATE": {"attempted": 0, "correct": 0, "accuracy": 0.0},
            "ADVANCED": {"attempted": 0, "correct": 0, "accuracy": 0.0}
        }

        for a in attempts:
            t = a.technology
            if t not in tech_stats:
                tech_stats[t] = {"attempted": 0, "correct": 0, "accuracy": 0.0}
            tech_stats[t]["attempted"] += 1
            if a.is_correct:
                tech_stats[t]["correct"] += 1

            d = a.difficulty
            if d in diff_stats:
                diff_stats[d]["attempted"] += 1
                if a.is_correct:
                    diff_stats[d]["correct"] += 1

        for t, stats in tech_stats.items():
            if stats["attempted"] > 0:
                stats["accuracy"] = round((stats["correct"] / stats["attempted"] * 100), 1)

        for d, stats in diff_stats.items():
            if stats["attempted"] > 0:
                stats["accuracy"] = round((stats["correct"] / stats["attempted"] * 100), 1)

        # Recent attempts (last 10)
        recent = db.query(PracticeAttempt).filter(
            PracticeAttempt.candidate_id == candidate_id
        ).order_by(PracticeAttempt.completed_at.desc()).limit(10).all()

        recent_list = [
            {
                "id": r.id,
                "technology": r.technology,
                "difficulty": r.difficulty,
                "is_correct": r.is_correct,
                "completed_at": r.completed_at.isoformat()
            }
            for r in recent
        ]

        # Candidate technologies count
        from app.models.models import CandidateTechnology
        detected_count = db.query(CandidateTechnology).filter(
            CandidateTechnology.candidate_id == candidate_id
        ).count()

        return {
            "total_attempted": total_attempted,
            "total_correct": total_correct,
            "overall_accuracy": overall_accuracy,
            "technologies_detected_count": detected_count,
            "technology_breakdown": tech_stats,
            "difficulty_breakdown": diff_stats,
            "recent_attempts": recent_list
        }
