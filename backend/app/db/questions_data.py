from app.models.models import QuestionDifficultyEnum

QUESTIONS_DATA = [
    # =========================================================================
    # 1. PYTHON (13 Questions)
    # =========================================================================
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Iterators & Generators",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which Python keyword transforms a standard function into a generator that yields values on demand?",
        "explanation": "The 'yield' statement pauses function execution and returns a generator iterator, producing values lazily without loading the entire collection into memory.",
        "marks": 1,
        "tags": ["python", "generators", "iterators"],
        "options": [
            {"key": "A", "text": "return", "is_correct": False},
            {"key": "B", "text": "yield", "is_correct": True},
            {"key": "C", "text": "generate", "is_correct": False},
            {"key": "D", "text": "async", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Mutability",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which of the following data types in Python is immutable?",
        "explanation": "Tuples in Python cannot be modified once instantiated, whereas lists, dictionaries, and sets are mutable collections.",
        "marks": 1,
        "tags": ["python", "data-types", "tuples"],
        "options": [
            {"key": "A", "text": "List", "is_correct": False},
            {"key": "B", "text": "Dictionary", "is_correct": False},
            {"key": "C", "text": "Tuple", "is_correct": True},
            {"key": "D", "text": "Set", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "List Comprehension",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does the expression '[x * 2 for x in range(4) if x % 2 == 0]' evaluate to?",
        "explanation": "range(4) produces 0, 1, 2, 3. The condition 'x % 2 == 0' selects 0 and 2. Multiplying by 2 results in [0, 4].",
        "marks": 1,
        "tags": ["python", "comprehension", "syntax"],
        "options": [
            {"key": "A", "text": "[0, 4]", "is_correct": True},
            {"key": "B", "text": "[0, 2, 4, 6]", "is_correct": False},
            {"key": "C", "text": "[2, 6]", "is_correct": False},
            {"key": "D", "text": "[0, 2]", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Default Arguments",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the primary risk of using a mutable object (like a list) as a default argument in a Python function?",
        "explanation": "Default argument expressions are evaluated once when the function definition is executed, so the same mutable instance is shared across subsequent calls.",
        "marks": 1,
        "tags": ["python", "functions", "pitfalls"],
        "options": [
            {"key": "A", "text": "The mutable object is shared across all function calls, retaining state changes", "is_correct": True},
            {"key": "B", "text": "Python raises a SyntaxError at compile time", "is_correct": False},
            {"key": "C", "text": "The function automatically converts the list into an immutable tuple", "is_correct": False},
            {"key": "D", "text": "The variable is garbage-collected immediately upon function exit", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Concurrency",
        "subtopic": "Global Interpreter Lock",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the primary role of Python's Global Interpreter Lock (GIL) in CPython?",
        "explanation": "The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecodes simultaneously, safeguarding memory management from race conditions.",
        "marks": 1,
        "tags": ["python", "concurrency", "gil", "threading"],
        "options": [
            {"key": "A", "text": "A mutex that prevents multiple native threads from executing Python bytecodes at once", "is_correct": True},
            {"key": "B", "text": "A compiler flag that enables JIT optimization across multiple CPUs", "is_correct": False},
            {"key": "C", "text": "A lock on the SQLite file used to prevent database corruption", "is_correct": False},
            {"key": "D", "text": "A garbage collection algorithm that clears cyclic references", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Advanced Features",
        "subtopic": "Decorators",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "In Python, how does the '@decorator' syntax alter the target function 'foo'?",
        "explanation": "Applying '@dec' above 'def foo(): ...' is equivalent to executing 'foo = dec(foo)', passing the original function and rebinding the identifier to the returned wrapper.",
        "marks": 1,
        "tags": ["python", "decorators", "metaprogramming"],
        "options": [
            {"key": "A", "text": "It executes foo = dec(foo) at function definition time", "is_correct": True},
            {"key": "B", "text": "It compiles foo into native C assembly bytecode", "is_correct": False},
            {"key": "C", "text": "It makes foo an immutable read-only object in memory", "is_correct": False},
            {"key": "D", "text": "It runs foo automatically in a background daemon thread", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Object Oriented Programming",
        "subtopic": "Dunder Methods",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which special method is invoked when the 'with' statement context is exited in Python?",
        "explanation": "The context manager protocol requires '__enter__' when entering the block and '__exit__' when leaving the block (handling exceptions if passed).",
        "marks": 1,
        "tags": ["python", "context-manager", "dunder"],
        "options": [
            {"key": "A", "text": "__close__", "is_correct": False},
            {"key": "B", "text": "__del__", "is_correct": False},
            {"key": "C", "text": "__exit__", "is_correct": True},
            {"key": "D", "text": "__leave__", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Core Language",
        "subtopic": "Memory & References",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the difference between the '==' operator and the 'is' operator in Python?",
        "explanation": "'==' checks for value equality (invoking '__eq__'), while 'is' checks for object identity (comparing memory addresses via 'id(a) == id(b)').",
        "marks": 1,
        "tags": ["python", "identity", "equality"],
        "options": [
            {"key": "A", "text": "'==' evaluates value equality, while 'is' evaluates reference identity", "is_correct": True},
            {"key": "B", "text": "'==' is strictly for integers, while 'is' compares string literals", "is_correct": False},
            {"key": "C", "text": "'is' is deprecated in Python 3 in favor of '=='", "is_correct": False},
            {"key": "D", "text": "'==' performs type checking, while 'is' converts types automatically", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Asynchronous Programming",
        "subtopic": "Asyncio",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What happens if a synchronous CPU-bound blocking call (e.g. time.sleep) is run inside an asyncio coroutine?",
        "explanation": "Synchronous blocking calls block the single-threaded event loop, starving all other concurrent coroutines and preventing pending tasks from progressing.",
        "marks": 1,
        "tags": ["python", "asyncio", "event-loop", "performance"],
        "options": [
            {"key": "A", "text": "The entire event loop is blocked, freezing all other concurrent tasks", "is_correct": True},
            {"key": "B", "text": "Asyncio automatically spawns an OS worker thread to handle it", "is_correct": False},
            {"key": "C", "text": "Python raises an immediate AsyncioConcurrencyException", "is_correct": False},
            {"key": "D", "text": "The operating system preemptively context-switches to the next coroutine", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Metaprogramming",
        "subtopic": "Metaclasses",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is a metaclass in Python?",
        "explanation": "A metaclass is the class of a class; it defines how a class object itself is constructed, validated, and instantiated, with 'type' being the default metaclass.",
        "marks": 1,
        "tags": ["python", "metaclasses", "oop"],
        "options": [
            {"key": "A", "text": "A class whose instances are classes themselves", "is_correct": True},
            {"key": "B", "text": "A decorative wrapper around external C-extensions", "is_correct": False},
            {"key": "C", "text": "A base class providing automatic JSON serialization", "is_correct": False},
            {"key": "D", "text": "A virtual interface specifying abstract methods", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Memory Management",
        "subtopic": "Garbage Collection",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How does CPython detect and reclaim circular reference memory leaks?",
        "explanation": "CPython uses reference counting as its primary mechanism, supplemented by a generational cyclic garbage collector that periodically detects reference cycles in container objects.",
        "marks": 1,
        "tags": ["python", "garbage-collection", "memory"],
        "options": [
            {"key": "A", "text": "Using a generational cyclic garbage collector that tracks container objects", "is_correct": True},
            {"key": "B", "text": "Exclusively using reference counting, which immediately frees all cyclic objects", "is_correct": False},
            {"key": "C", "text": "By executing a Stop-The-World mark-and-sweep sweep every 60 seconds", "is_correct": False},
            {"key": "D", "text": "CPython cannot reclaim circular references without manual 'del' calls", "is_correct": False}
        ]
    },
    {
        "technology": "Python",
        "topic": "Advanced Features",
        "subtopic": "__slots__",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary benefit of declaring '__slots__' in a Python class definition?",
        "explanation": "Declaring '__slots__' prevents the creation of the default instance '__dict__', dramatically reducing per-instance memory consumption and slightly improving attribute access speed.",
        "marks": 1,
        "tags": ["python", "memory", "slots", "optimization"],
        "options": [
            {"key": "A", "text": "It suppresses instance '__dict__' creation, minimizing memory footprint", "is_correct": True},
            {"key": "B", "text": "It automatically synchronizes class attributes across multiprocessing workers", "is_correct": False},
            {"key": "C", "text": "It forces static compile-time type checking on all attributes", "is_correct": False},
            {"key": "D", "text": "It encrypts object attributes in memory for security", "is_correct": False}
        ]
    },

    # =========================================================================
    # 2. JAVA (13 Questions)
    # =========================================================================
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "OOP Principles",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which Java keyword is used to inherit a class in Java?",
        "explanation": "The 'extends' keyword is used to derive a subclass from a superclass, whereas 'implements' is used for interfaces.",
        "marks": 1,
        "tags": ["java", "oop", "inheritance"],
        "options": [
            {"key": "A", "text": "implements", "is_correct": False},
            {"key": "B", "text": "extends", "is_correct": True},
            {"key": "C", "text": "inherits", "is_correct": False},
            {"key": "D", "text": "derives", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "Access Modifiers",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which access modifier in Java restricts member visibility to the containing package only (default package-private)?",
        "explanation": "When no modifier is specified, Java applies package-private access, making members visible only within classes of the same package.",
        "marks": 1,
        "tags": ["java", "access-modifiers", "scope"],
        "options": [
            {"key": "A", "text": "protected", "is_correct": False},
            {"key": "B", "text": "private", "is_correct": False},
            {"key": "C", "text": "No modifier (package-private)", "is_correct": True},
            {"key": "D", "text": "public", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "Primitive Types",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the default value of a boolean field in a Java class?",
        "explanation": "Instance and static boolean variables in Java default to 'false' upon uninitialized object instantiation.",
        "marks": 1,
        "tags": ["java", "primitives", "defaults"],
        "options": [
            {"key": "A", "text": "true", "is_correct": False},
            {"key": "B", "text": "false", "is_correct": True},
            {"key": "C", "text": "null", "is_correct": False},
            {"key": "D", "text": "0", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "Exceptions",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which block in a Java try-catch statement is guaranteed to execute regardless of whether an exception is thrown?",
        "explanation": "The 'finally' block always executes after try/catch, typically used to release system resources, unless System.exit() is invoked.",
        "marks": 1,
        "tags": ["java", "exceptions", "control-flow"],
        "options": [
            {"key": "A", "text": "catch", "is_correct": False},
            {"key": "B", "text": "throw", "is_correct": False},
            {"key": "C", "text": "finally", "is_correct": True},
            {"key": "D", "text": "complete", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Collections Framework",
        "subtopic": "HashMap Internals",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does Java 8's HashMap handle severe hash collision bucket degradation?",
        "explanation": "Once a collision bucket exceeds TREEIFY_THRESHOLD (8 entries) and table capacity >= 64, HashMap transforms the linked list into a balanced Red-Black Tree, improving lookup from O(n) to O(log n).",
        "marks": 1,
        "tags": ["java", "collections", "hashmap", "data-structures"],
        "options": [
            {"key": "A", "text": "It converts the bucket's linked list into a Red-Black Tree when bucket size exceeds 8", "is_correct": True},
            {"key": "B", "text": "It immediately drops oldest entries using an LRU eviction policy", "is_correct": False},
            {"key": "C", "text": "It throws an unchecked ConcurrentModificationException", "is_correct": False},
            {"key": "D", "text": "It creates a nested secondary hash table inside the bucket", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Concurrency",
        "subtopic": "Synchronization",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What guarantee does the 'volatile' keyword provide in Java?",
        "explanation": "'volatile' guarantees visibility of changes across threads (reads and writes go directly to main memory rather than CPU cache) and prevents instruction reordering, but does not guarantee atomic compound operations.",
        "marks": 1,
        "tags": ["java", "concurrency", "volatile", "memory-model"],
        "options": [
            {"key": "A", "text": "Variable reads and writes are visible immediately across all threads without CPU cache staleness", "is_correct": True},
            {"key": "B", "text": "It makes compound increment operations (i++) strictly atomic", "is_correct": False},
            {"key": "C", "text": "It locks the containing object monitor across all methods", "is_correct": False},
            {"key": "D", "text": "It marks the variable for serialization exclusion", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "String Pool",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does String.intern() do in Java?",
        "explanation": "String.intern() searches the JVM String Constant Pool for an equivalent string. If present, it returns that canonical instance; otherwise, it adds the string to the pool and returns its reference.",
        "marks": 1,
        "tags": ["java", "strings", "jvm", "memory"],
        "options": [
            {"key": "A", "text": "Returns the canonical representation of the string from the JVM String Constant Pool", "is_correct": True},
            {"key": "B", "text": "Encrypts the string bytes using UTF-16 encoding", "is_correct": False},
            {"key": "C", "text": "Converts the string into a mutable character array", "is_correct": False},
            {"key": "D", "text": "Permanently locks the string against garbage collection", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Streams & Lambdas",
        "subtopic": "Functional Interfaces",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which functional interface in 'java.util.function' accepts one argument and returns a boolean value?",
        "explanation": "A 'Predicate<T>' represents a boolean-valued function of one argument, taking an input of type T and returning a boolean.",
        "marks": 1,
        "tags": ["java", "functional", "streams", "lambdas"],
        "options": [
            {"key": "A", "text": "Consumer<T>", "is_correct": False},
            {"key": "B", "text": "Supplier<T>", "is_correct": False},
            {"key": "C", "text": "Predicate<T>", "is_correct": True},
            {"key": "D", "text": "Function<T, R>", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "JVM & Memory",
        "subtopic": "Garbage Collectors",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What distinguishes the Z Garbage Collector (ZGC) in modern Java?",
        "explanation": "ZGC is a scalable, low-latency concurrent garbage collector that performs all expensive work concurrently with application threads, keeping pause times under 1 millisecond regardless of heap size.",
        "marks": 1,
        "tags": ["java", "jvm", "zgc", "performance"],
        "options": [
            {"key": "A", "text": "It executes concurrent reference processing with pause times under 1ms, scalable to terabyte heaps", "is_correct": True},
            {"key": "B", "text": "It is a non-generational single-threaded Stop-The-World collector", "is_correct": False},
            {"key": "C", "text": "It runs exclusively on 32-bit embedded JVM architectures", "is_correct": False},
            {"key": "D", "text": "It replaces stack frames with off-heap direct byte buffers", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "JVM & Memory",
        "subtopic": "ClassLoaders",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How does Java's ClassLoader delegation model operate?",
        "explanation": "When requested to load a class, a ClassLoader first delegates the request to its parent ClassLoader before attempting to find and load the class bytecodes itself.",
        "marks": 1,
        "tags": ["java", "classloaders", "jvm"],
        "options": [
            {"key": "A", "text": "A classloader delegates loading to its parent first before attempting to load the class itself", "is_correct": True},
            {"key": "B", "text": "The custom child classloader always overrides and loads classes before parent consultation", "is_correct": False},
            {"key": "C", "text": "All classloaders load classes in parallel using an atomic round-robin dispatch", "is_correct": False},
            {"key": "D", "text": "Classes are compiled directly into JIT native code without bytecode verification", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Concurrency",
        "subtopic": "Memory Model",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In the Java Memory Model (JMM), what does the 'happens-before' relationship establish?",
        "explanation": "The 'happens-before' relation provides an ordering guarantee ensuring that memory writes by one action are guaranteed to be visible to another action across threads.",
        "marks": 1,
        "tags": ["java", "jmm", "concurrency", "multithreading"],
        "options": [
            {"key": "A", "text": "A formal guarantee that memory writes by one thread are visible to specific reads in another", "is_correct": True},
            {"key": "B", "text": "A CPU clock cycle priority rule that prevents thread deadlocks", "is_correct": False},
            {"key": "C", "text": "A compile-time lint rule prohibiting nested synchronized statements", "is_correct": False},
            {"key": "D", "text": "A garbage collector heuristic determining object allocation in Eden space", "is_correct": False}
        ]
    },
    {
        "technology": "Java",
        "topic": "Core Language",
        "subtopic": "Generics & Type Erasure",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the consequence of Type Erasure in Java Generics?",
        "explanation": "Type parameters are erased at compile-time and replaced with their bounds (or Object), meaning generic type arguments (e.g. List<String> vs List<Integer>) are indistinguishable at runtime via reflection or instanceof.",
        "marks": 1,
        "tags": ["java", "generics", "type-erasure"],
        "options": [
            {"key": "A", "text": "Type parameters are replaced with their upper bounds, so generic types cannot be checked via instanceof at runtime", "is_correct": True},
            {"key": "B", "text": "Generic objects are converted into native C struct pointers", "is_correct": False},
            {"key": "C", "text": "The JVM duplicates bytecode for every distinct primitive type argument", "is_correct": False},
            {"key": "D", "text": "Generic collections become read-only immutable instances", "is_correct": False}
        ]
    },

    # =========================================================================
    # 3. C++ (12 Questions)
    # =========================================================================
    {
        "technology": "C++",
        "topic": "Core Language",
        "subtopic": "Pointers & References",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which operator is used to obtain the memory address of a variable in C++?",
        "explanation": "The address-of operator '&' returns the memory address of an object, while '*' is the dereference operator.",
        "marks": 1,
        "tags": ["c++", "pointers", "basics"],
        "options": [
            {"key": "A", "text": "*", "is_correct": False},
            {"key": "B", "text": "&", "is_correct": True},
            {"key": "C", "text": "->", "is_correct": False},
            {"key": "D", "text": "::", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Core Language",
        "subtopic": "Memory Allocation",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which pair of operators is used for dynamic memory allocation and deallocation on the heap in C++?",
        "explanation": "In C++, 'new' dynamically allocates memory from the free store and calls constructors, while 'delete' calls destructors and deallocates memory.",
        "marks": 1,
        "tags": ["c++", "memory", "heap"],
        "options": [
            {"key": "A", "text": "malloc and free", "is_correct": False},
            {"key": "B", "text": "new and delete", "is_correct": True},
            {"key": "C", "text": "alloc and dealloc", "is_correct": False},
            {"key": "D", "text": "create and destroy", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Object Oriented Programming",
        "subtopic": "Access Specifiers",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the default member access specifier in a C++ 'class' versus a 'struct'?",
        "explanation": "Members of a 'class' are private by default, whereas members of a 'struct' are public by default.",
        "marks": 1,
        "tags": ["c++", "classes", "structs", "oop"],
        "options": [
            {"key": "A", "text": "Class members are private by default; struct members are public by default", "is_correct": True},
            {"key": "B", "text": "Class members are public by default; struct members are private by default", "is_correct": False},
            {"key": "C", "text": "Both class and struct default to protected access", "is_correct": False},
            {"key": "D", "text": "Both class and struct default to public access", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Core Language",
        "subtopic": "Constructors",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "When is a destructor called in C++?",
        "explanation": "Destructors execute automatically when an automatic (stack) object goes out of scope or when 'delete' is called on a heap pointer.",
        "marks": 1,
        "tags": ["c++", "destructors", "raii"],
        "options": [
            {"key": "A", "text": "When an object goes out of scope or is explicitly deleted", "is_correct": True},
            {"key": "B", "text": "Only when the operating system shuts down the process", "is_correct": False},
            {"key": "C", "text": "Immediately before the constructor finishes executing", "is_correct": False},
            {"key": "D", "text": "When an object is copied by value", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Memory Management",
        "subtopic": "Smart Pointers",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Why cannot a 'std::unique_ptr' be copied by value in C++?",
        "explanation": "'std::unique_ptr' enforces exclusive ownership semantics; its copy constructor and copy assignment operator are explicitly deleted (= delete). It can only be moved.",
        "marks": 1,
        "tags": ["c++", "smart-pointers", "move-semantics"],
        "options": [
            {"key": "A", "text": "Its copy constructor and assignment operators are deleted to guarantee exclusive ownership", "is_correct": True},
            {"key": "B", "text": "It contains a volatile atomic reference counter that blocks copying", "is_correct": False},
            {"key": "C", "text": "C++ does not permit templates to define copy constructors", "is_correct": False},
            {"key": "D", "text": "Copying unique_ptr causes an immediate segmentation fault at runtime", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Object Oriented Programming",
        "subtopic": "Virtual Functions",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the purpose of declaring a base class destructor as 'virtual' in C++?",
        "explanation": "If a base class pointer deletes a derived class object without a virtual destructor, only the base destructor executes, resulting in undefined behavior and resource leaks.",
        "marks": 1,
        "tags": ["c++", "polymorphism", "virtual", "destructors"],
        "options": [
            {"key": "A", "text": "To ensure the derived class destructor is called when deleting an object via a base pointer", "is_correct": True},
            {"key": "B", "text": "To force all derived classes to make their own destructors private", "is_correct": False},
            {"key": "C", "text": "To allocate the object in read-only code memory", "is_correct": False},
            {"key": "D", "text": "To prevent the class from being instantiated", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Standard Template Library",
        "subtopic": "Vector Growth",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the amortized time complexity of inserting an element at the end of a 'std::vector' in C++?",
        "explanation": "While vector reallocation and copying takes O(n), geometric capacity growth (typically 1.5x or 2x) guarantees an amortized time complexity of O(1) for push_back.",
        "marks": 1,
        "tags": ["c++", "stl", "vector", "complexity"],
        "options": [
            {"key": "A", "text": "O(1) amortized", "is_correct": True},
            {"key": "B", "text": "O(n) strict worst-case always", "is_correct": False},
            {"key": "C", "text": "O(log n)", "is_correct": False},
            {"key": "D", "text": "O(n log n)", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Core Language",
        "subtopic": "Move Semantics",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does 'std::move' actually do in C++11?",
        "explanation": "'std::move' does not move anything at runtime; it performs an unconditional static_cast of its argument to an rvalue reference (T&&), enabling move constructor/assignment selection.",
        "marks": 1,
        "tags": ["c++", "move-semantics", "rvalue", "casting"],
        "options": [
            {"key": "A", "text": "It unconditionally casts an expression to an rvalue reference (T&&)", "is_correct": True},
            {"key": "B", "text": "It physically copies memory bytes using memcpy", "is_correct": False},
            {"key": "C", "text": "It zeros out the original object's memory immediately", "is_correct": False},
            {"key": "D", "text": "It creates a background OS thread to transfer data", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Memory & Performance",
        "subtopic": "RAII",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the core guarantee of the RAII (Resource Acquisition Is Initialization) idiom?",
        "explanation": "RAII binds the lifecycle of a resource (memory, file handle, lock) to object lifetime, guaranteeing automatic cleanup during stack unwinding upon normal exit or exceptions.",
        "marks": 1,
        "tags": ["c++", "raii", "memory", "safety"],
        "options": [
            {"key": "A", "text": "Resource lifetime is bound to object lifetime, ensuring cleanup upon stack unwinding", "is_correct": True},
            {"key": "B", "text": "All heap memory is verified by an embedded runtime garbage collector", "is_correct": False},
            {"key": "C", "text": "Variables are initialized strictly at compile-time as constexpr values", "is_correct": False},
            {"key": "D", "text": "Memory addresses are randomized to defeat buffer overflow exploits", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Metaprogramming",
        "subtopic": "Templates & SFINAE",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In C++ template metaprogramming, what does SFINAE stand for?",
        "explanation": "SFINAE stands for 'Substitution Failure Is Not An Error'. When substituting deduced types fails in template overloads, the compiler discards the overload rather than failing with a compilation error.",
        "marks": 1,
        "tags": ["c++", "templates", "sfinae", "metaprogramming"],
        "options": [
            {"key": "A", "text": "Substitution Failure Is Not An Error", "is_correct": True},
            {"key": "B", "text": "Static Function Invocation And Execution", "is_correct": False},
            {"key": "C", "text": "Sequential Floating Instruction Architecture", "is_correct": False},
            {"key": "D", "text": "Standard Framework Interface Node Algorithm", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Concurrency",
        "subtopic": "Memory Model & Atomics",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does 'std::memory_order_relaxed' guarantee in C++ atomic operations?",
        "explanation": "'memory_order_relaxed' only guarantees atomicity of the operation on that specific variable, with no synchronization or ordering constraints relative to other memory accesses.",
        "marks": 1,
        "tags": ["c++", "atomics", "concurrency", "memory-order"],
        "options": [
            {"key": "A", "text": "Atomicity of the target operation only, without inter-thread ordering or memory synchronization", "is_correct": True},
            {"key": "B", "text": "Sequential consistency across all CPU cores and caches", "is_correct": False},
            {"key": "C", "text": "Acquire-release synchronization paired with an explicit memory fence", "is_correct": False},
            {"key": "D", "text": "Total store ordering with hardware bus lock", "is_correct": False}
        ]
    },
    {
        "technology": "C++",
        "topic": "Object Oriented Programming",
        "subtopic": "Vtable & Vptr",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How do C++ compilers implement dynamic dispatch for virtual member functions?",
        "explanation": "Compilers generate a virtual table (vtable) containing function pointers for each polymorphic class, and store a hidden virtual table pointer (vptr) inside each object instance.",
        "marks": 1,
        "tags": ["c++", "vtable", "polymorphism", "internals"],
        "options": [
            {"key": "A", "text": "Using a virtual method table (vtable) indexed by a virtual pointer (vptr) in the object", "is_correct": True},
            {"key": "B", "text": "Using runtime string hash lookups against class symbol tables", "is_correct": False},
            {"key": "C", "text": "By dynamically recompiling calls into inline assembly stubs", "is_correct": False},
            {"key": "D", "text": "By querying operating system dispatch queues via IPC", "is_correct": False}
        ]
    },

    # =========================================================================
    # 4. SQL (12 Questions)
    # =========================================================================
    {
        "technology": "SQL",
        "topic": "Querying",
        "subtopic": "Basic Clauses",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which SQL clause is used to filter rows returned by a SELECT query based on a specified condition?",
        "explanation": "The 'WHERE' clause filters rows before any grouping occurs, while 'HAVING' filters aggregated groups.",
        "marks": 1,
        "tags": ["sql", "select", "where", "filtering"],
        "options": [
            {"key": "A", "text": "ORDER BY", "is_correct": False},
            {"key": "B", "text": "WHERE", "is_correct": True},
            {"key": "C", "text": "GROUP BY", "is_correct": False},
            {"key": "D", "text": "HAVING", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Joins",
        "subtopic": "Join Types",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which SQL join returns all records from the left table and the matched records from the right table?",
        "explanation": "A LEFT JOIN (or LEFT OUTER JOIN) returns all rows from the left table, with NULL values for right table columns when no match exists.",
        "marks": 1,
        "tags": ["sql", "joins", "left-join"],
        "options": [
            {"key": "A", "text": "INNER JOIN", "is_correct": False},
            {"key": "B", "text": "LEFT JOIN", "is_correct": True},
            {"key": "C", "text": "RIGHT JOIN", "is_correct": False},
            {"key": "D", "text": "FULL JOIN", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Aggregations",
        "subtopic": "Aggregate Functions",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which aggregate function calculates the total number of non-null values in a specified column?",
        "explanation": "COUNT(column_name) returns the count of non-null values in that column, whereas COUNT(*) counts all rows.",
        "marks": 1,
        "tags": ["sql", "aggregations", "count"],
        "options": [
            {"key": "A", "text": "SUM()", "is_correct": False},
            {"key": "B", "text": "TOTAL()", "is_correct": False},
            {"key": "C", "text": "COUNT()", "is_correct": True},
            {"key": "D", "text": "AVG()", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Data Modification",
        "subtopic": "DML Operations",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which SQL statement is used to remove all rows from a table without logging individual row deletions?",
        "explanation": "TRUNCATE TABLE removes all rows rapidly by deallocating data pages, generating minimal transaction logs compared to DELETE.",
        "marks": 1,
        "tags": ["sql", "dml", "truncate"],
        "options": [
            {"key": "A", "text": "DELETE", "is_correct": False},
            {"key": "B", "text": "TRUNCATE", "is_correct": True},
            {"key": "C", "text": "DROP", "is_correct": False},
            {"key": "D", "text": "REMOVE", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Grouping & Filtering",
        "subtopic": "HAVING vs WHERE",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the critical semantic difference between WHERE and HAVING in SQL?",
        "explanation": "'WHERE' filters individual rows before aggregation occurs; 'HAVING' filters grouped records after 'GROUP BY' aggregation functions execute.",
        "marks": 1,
        "tags": ["sql", "having", "where", "grouping"],
        "options": [
            {"key": "A", "text": "WHERE filters rows before aggregation, while HAVING filters aggregated groups", "is_correct": True},
            {"key": "B", "text": "WHERE is only used for strings, while HAVING is strictly for numeric columns", "is_correct": False},
            {"key": "C", "text": "HAVING cannot be used without an ORDER BY clause", "is_correct": False},
            {"key": "D", "text": "There is no difference; they are interchangeable aliases", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Querying",
        "subtopic": "NULL Handling",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "In three-valued SQL logic, what is the result of evaluating 'NULL = NULL'?",
        "explanation": "In SQL three-valued logic (TRUE, FALSE, UNKNOWN), comparing NULL using '=' yields UNKNOWN (falsy in WHERE filters). The IS NULL predicate must be used.",
        "marks": 1,
        "tags": ["sql", "null", "logic"],
        "options": [
            {"key": "A", "text": "UNKNOWN", "is_correct": True},
            {"key": "B", "text": "TRUE", "is_correct": False},
            {"key": "C", "text": "FALSE", "is_correct": False},
            {"key": "D", "text": "SyntaxError", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Subqueries",
        "subtopic": "Common Table Expressions",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which SQL clause initiates a Common Table Expression (CTE)?",
        "explanation": "A CTE is declared using the 'WITH' keyword, creating a temporary named result set accessible within the scope of the main query.",
        "marks": 1,
        "tags": ["sql", "cte", "with"],
        "options": [
            {"key": "A", "text": "DECLARE", "is_correct": False},
            {"key": "B", "text": "WITH", "is_correct": True},
            {"key": "C", "text": "TEMPORARY", "is_correct": False},
            {"key": "D", "text": "LET", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Set Operations",
        "subtopic": "UNION vs UNION ALL",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does 'UNION ALL' differ from 'UNION' in SQL performance and results?",
        "explanation": "'UNION' performs a sort/deduplication step to remove duplicate rows between result sets, whereas 'UNION ALL' concatenates sets directly without deduplication overhead.",
        "marks": 1,
        "tags": ["sql", "union", "union-all", "performance"],
        "options": [
            {"key": "A", "text": "'UNION ALL' retains duplicate rows and is faster because it avoids sorting for distinct values", "is_correct": True},
            {"key": "B", "text": "'UNION ALL' eliminates duplicates, while 'UNION' preserves them", "is_correct": False},
            {"key": "C", "text": "'UNION ALL' is only valid between tables with identical column names", "is_correct": False},
            {"key": "D", "text": "'UNION' executes in parallel, whereas 'UNION ALL' runs single-threaded", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Window Functions",
        "subtopic": "Ranking",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the difference between RANK() and DENSE_RANK() in SQL window functions?",
        "explanation": "When handling ties, RANK() skips rank numbers corresponding to the number of tied positions (e.g., 1, 2, 2, 4), while DENSE_RANK() produces consecutive rank integers without gaps (e.g., 1, 2, 2, 3).",
        "marks": 1,
        "tags": ["sql", "window-functions", "rank", "dense-rank"],
        "options": [
            {"key": "A", "text": "RANK() leaves gaps in sequence following ties; DENSE_RANK() assigns consecutive numbers without gaps", "is_correct": True},
            {"key": "B", "text": "RANK() is non-deterministic, while DENSE_RANK() requires an explicit partition key", "is_correct": False},
            {"key": "C", "text": "DENSE_RANK() can only be computed over numeric integer columns", "is_correct": False},
            {"key": "D", "text": "RANK() operates only on indexed columns, whereas DENSE_RANK() works on all columns", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Window Functions",
        "subtopic": "Frames & Partitioning",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does the window frame clause 'ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW' accomplish?",
        "explanation": "It defines a cumulative running aggregation frame from the start of the partition up to and including the current row.",
        "marks": 1,
        "tags": ["sql", "window-functions", "running-total"],
        "options": [
            {"key": "A", "text": "Computes a cumulative running aggregation from the first row of the partition to the current row", "is_correct": True},
            {"key": "B", "text": "Calculates the total sum of the entire table regardless of partition", "is_correct": False},
            {"key": "C", "text": "Averages only the current row and its immediate predecessor", "is_correct": False},
            {"key": "D", "text": "Filters out rows where the preceding value is NULL", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Query Optimization",
        "subtopic": "Correlated Subqueries",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why can correlated subqueries cause significant query performance degradation?",
        "explanation": "Correlated subqueries reference columns from the outer query, meaning the subquery may be evaluated repeatedly for each candidate row processed by the outer query (O(n * m)).",
        "marks": 1,
        "tags": ["sql", "optimization", "subqueries", "performance"],
        "options": [
            {"key": "A", "text": "They may re-execute for every candidate row evaluated by the outer query", "is_correct": True},
            {"key": "B", "text": "They force the database engine to disable all secondary B-tree indexes", "is_correct": False},
            {"key": "C", "text": "They invalidate transaction logs and cause table lock escalation", "is_correct": False},
            {"key": "D", "text": "They cannot return boolean expressions", "is_correct": False}
        ]
    },
    {
        "technology": "SQL",
        "topic": "Transactions",
        "subtopic": "ACID Properties",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In the SQL standard, which isolation level prevents Dirty Reads and Non-Repeatable Reads, but still permits Phantom Reads?",
        "explanation": "REPEATABLE READ prevents Dirty Reads and Non-Repeatable Reads. Phantom Reads (where new rows inserted by concurrent transactions appear upon re-querying) are only fully prevented by SERIALIZABLE.",
        "marks": 1,
        "tags": ["sql", "acid", "isolation-levels", "transactions"],
        "options": [
            {"key": "A", "text": "REPEATABLE READ", "is_correct": True},
            {"key": "B", "text": "READ COMMITTED", "is_correct": False},
            {"key": "C", "text": "SERIALIZABLE", "is_correct": False},
            {"key": "D", "text": "READ UNCOMMITTED", "is_correct": False}
        ]
    },

    # =========================================================================
    # 5. DBMS (12 Questions)
    # =========================================================================
    {
        "technology": "DBMS",
        "topic": "Architecture",
        "subtopic": "Keys",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What are the two primary requirements of a Primary Key in relational databases?",
        "explanation": "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        "marks": 1,
        "tags": ["dbms", "primary-key", "keys"],
        "options": [
            {"key": "A", "text": "It must contain unique values and cannot contain NULLs", "is_correct": True},
            {"key": "B", "text": "It must be an auto-incrementing 32-bit integer", "is_correct": False},
            {"key": "C", "text": "It must reference a foreign key in another table", "is_correct": False},
            {"key": "D", "text": "It must be encrypted using SHA-256", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Architecture",
        "subtopic": "Relational Model",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "In relational database terminology, what is a tuple?",
        "explanation": "In relational calculus and database theory, a tuple corresponds to a single row (or record) in a relation (table).",
        "marks": 1,
        "tags": ["dbms", "relational-model", "terminology"],
        "options": [
            {"key": "A", "text": "A column or attribute", "is_correct": False},
            {"key": "B", "text": "A row or record", "is_correct": True},
            {"key": "C", "text": "A database schema definition", "is_correct": False},
            {"key": "D", "text": "An index node in a B-Tree", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Normalization",
        "subtopic": "1NF",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the fundamental requirement for a table to satisfy First Normal Form (1NF)?",
        "explanation": "First Normal Form requires that every column value is atomic (indivisible) and each record is unique, eliminating repeating groups or arrays.",
        "marks": 1,
        "tags": ["dbms", "normalization", "1nf"],
        "options": [
            {"key": "A", "text": "All attribute values must be atomic with no repeating groups", "is_correct": True},
            {"key": "B", "text": "All non-key attributes must be fully functionally dependent on the entire primary key", "is_correct": False},
            {"key": "C", "text": "No transitive dependencies may exist between non-prime attributes", "is_correct": False},
            {"key": "D", "text": "Foreign keys must use ON DELETE CASCADE", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "ACID Properties",
        "subtopic": "Durability",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does the 'Durability' property in ACID transactions ensure?",
        "explanation": "Durability guarantees that once a transaction commits, its state modifications persist permanently even in the event of an abrupt system crash or power outage.",
        "marks": 1,
        "tags": ["dbms", "acid", "durability"],
        "options": [
            {"key": "A", "text": "Committed data is saved permanently and survives system crashes", "is_correct": True},
            {"key": "B", "text": "Transactions execute in total isolation from concurrent transactions", "is_correct": False},
            {"key": "C", "text": "Either all statements in a transaction succeed, or all are rolled back", "is_correct": False},
            {"key": "D", "text": "Data constraints and integrity checks are never violated", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Indexing",
        "subtopic": "B+ Trees",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Why do relational databases predominantly use B+ Trees instead of standard Binary Search Trees for disk-based indexing?",
        "explanation": "B+ Trees have high fan-out (low tree depth), drastically minimizing disk I/O seeks. Furthermore, leaf nodes are linked sequentially, enabling fast range scans.",
        "marks": 1,
        "tags": ["dbms", "indexing", "b-plus-tree", "storage"],
        "options": [
            {"key": "A", "text": "High fan-out minimizes disk I/O seek operations, and linked leaves enable efficient range scans", "is_correct": True},
            {"key": "B", "text": "B+ Trees consume zero disk storage by using CPU cache lines", "is_correct": False},
            {"key": "C", "text": "Binary search trees cannot support string keys", "is_correct": False},
            {"key": "D", "text": "B+ Trees eliminate the need for write-ahead logging", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Normalization",
        "subtopic": "3NF vs BCNF",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Under Boyce-Codd Normal Form (BCNF), what condition must hold for every non-trivial functional dependency X -> Y?",
        "explanation": "In BCNF, for every functional dependency X -> Y, X must be a superkey of the relation.",
        "marks": 1,
        "tags": ["dbms", "normalization", "bcnf", "dependencies"],
        "options": [
            {"key": "A", "text": "X must be a superkey", "is_correct": True},
            {"key": "B", "text": "Y must be a prime attribute", "is_correct": False},
            {"key": "C", "text": "X and Y must belong to the same composite key", "is_correct": False},
            {"key": "D", "text": "The dependency must be derived from a foreign key constraint", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Concurrency Control",
        "subtopic": "Deadlock Detection",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does a DBMS detect deadlocks in lock-based concurrency control?",
        "explanation": "A DBMS constructs a Wait-For Graph (WFG) where vertices represent transactions and edges represent lock dependencies. A cycle in the WFG indicates a deadlock.",
        "marks": 1,
        "tags": ["dbms", "deadlocks", "concurrency", "wfg"],
        "options": [
            {"key": "A", "text": "By detecting cycles in a Wait-For Graph (WFG) of active transactions", "is_correct": True},
            {"key": "B", "text": "By calculating the CPU temperature of the database server", "is_correct": False},
            {"key": "C", "text": "By restricting the database to single-threaded transaction execution", "is_correct": False},
            {"key": "D", "text": "By aborting all transactions that run longer than 500 milliseconds", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Storage Engine",
        "subtopic": "Write-Ahead Logging",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the WAL (Write-Ahead Logging) protocol rule in database recovery management?",
        "explanation": "Under the WAL protocol, log records describing database updates must be flushed to non-volatile disk before the corresponding dirty data pages are written to the database files.",
        "marks": 1,
        "tags": ["dbms", "wal", "recovery", "storage"],
        "options": [
            {"key": "A", "text": "Log records must be written to disk before corresponding dirty data pages are flushed", "is_correct": True},
            {"key": "B", "text": "Data pages are updated on disk before any logging is performed", "is_correct": False},
            {"key": "C", "text": "Logs are kept only in RAM and discarded upon clean server shutdown", "is_correct": False},
            {"key": "D", "text": "Transactions cannot commit until all data tables are backed up", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Concurrency Control",
        "subtopic": "Two-Phase Locking (2PL)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What does Strict Two-Phase Locking (Strict 2PL) enforce regarding exclusive locks?",
        "explanation": "Strict 2PL requires that all exclusive (write) locks acquired by a transaction must be held until the transaction commits or aborts, preventing cascading aborts.",
        "marks": 1,
        "tags": ["dbms", "2pl", "concurrency", "locking"],
        "options": [
            {"key": "A", "text": "All exclusive locks must be held until transaction commit or rollback, preventing cascading aborts", "is_correct": True},
            {"key": "B", "text": "Locks can be released at any time during the growing phase", "is_correct": False},
            {"key": "C", "text": "Only shared read locks are permitted; write locks are converted to optimistic timestamps", "is_correct": False},
            {"key": "D", "text": "It guarantees that deadlocks cannot occur under any circumstance", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Concurrency Control",
        "subtopic": "MVCC",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How does Multi-Version Concurrency Control (MVCC) eliminate read-write contention in engines like PostgreSQL and InnoDB?",
        "explanation": "MVCC maintains multiple versions of data rows with transaction timestamps/IDs, so readers read a consistent snapshot of the data without locking, meaning readers do not block writers and writers do not block readers.",
        "marks": 1,
        "tags": ["dbms", "mvcc", "postgresql", "concurrency"],
        "options": [
            {"key": "A", "text": "Readers access a consistent historical snapshot without acquiring read locks, so readers do not block writers", "is_correct": True},
            {"key": "B", "text": "All reads and writes acquire table-level exclusive locks in strict order", "is_correct": False},
            {"key": "C", "text": "Writes are cached in client browser cookies until verified", "is_correct": False},
            {"key": "D", "text": "Database tables are duplicated onto secondary read-only SSD drives", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Recovery",
        "subtopic": "ARIES Algorithm",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What are the three distinct phases of the ARIES database recovery algorithm?",
        "explanation": "ARIES recovery executes Analysis (identifying dirty pages and active transactions at crash), Redo (repeating history to restore state), and Undo (rolling back uncommitted transactions).",
        "marks": 1,
        "tags": ["dbms", "aries", "recovery", "algorithms"],
        "options": [
            {"key": "A", "text": "Analysis, Redo, and Undo", "is_correct": True},
            {"key": "B", "text": "Compile, Optimize, and Execute", "is_correct": False},
            {"key": "C", "text": "Lock, Mutate, and Unlock", "is_correct": False},
            {"key": "D", "text": "Replicate, Shard, and Partition", "is_correct": False}
        ]
    },
    {
        "technology": "DBMS",
        "topic": "Distributed Databases",
        "subtopic": "CAP Theorem",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "According to Eric Brewer's CAP Theorem, what must a distributed data system trade off during a network partition (P)?",
        "explanation": "Under network partition (P), a distributed system must choose between Consistency (all nodes see identical data) and Availability (every non-failing node returns a response).",
        "marks": 1,
        "tags": ["dbms", "cap-theorem", "distributed-systems"],
        "options": [
            {"key": "A", "text": "It must choose between Consistency (C) and Availability (A)", "is_correct": True},
            {"key": "B", "text": "It must sacrifice Persistence for Speed", "is_correct": False},
            {"key": "C", "text": "It must convert all tables into key-value stores", "is_correct": False},
            {"key": "D", "text": "It must drop ACID transactions in favor of full rollback", "is_correct": False}
        ]
    },

    # =========================================================================
    # 6. DSA (13 Questions)
    # =========================================================================
    {
        "technology": "DSA",
        "topic": "Linear Data Structures",
        "subtopic": "Stacks",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which principle governs the order of operations in a Stack data structure?",
        "explanation": "A stack follows the LIFO (Last In, First Out) principle, where the most recently pushed element is the first to be popped.",
        "marks": 1,
        "tags": ["dsa", "stack", "lifo"],
        "options": [
            {"key": "A", "text": "FIFO (First In, First Out)", "is_correct": False},
            {"key": "B", "text": "LIFO (Last In, First Out)", "is_correct": True},
            {"key": "C", "text": "Priority based", "is_correct": False},
            {"key": "D", "text": "Random access", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Searching Algorithms",
        "subtopic": "Binary Search",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What prerequisite must be satisfied to perform Binary Search on an array?",
        "explanation": "Binary search divides the search space in half at each step, which requires the underlying elements to be sorted in monotonic order.",
        "marks": 1,
        "tags": ["dsa", "binary-search", "algorithms"],
        "options": [
            {"key": "A", "text": "The array must be sorted", "is_correct": True},
            {"key": "B", "text": "The array must contain only positive integers", "is_correct": False},
            {"key": "C", "text": "The array size must be a power of two", "is_correct": False},
            {"key": "D", "text": "The array must be dynamically allocated on the heap", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Linear Data Structures",
        "subtopic": "Linked Lists",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the time complexity to insert a node at the head of a Singly Linked List?",
        "explanation": "Inserting at the head requires creating the node, pointing its next pointer to the current head, and updating the head pointer, taking O(1) time.",
        "marks": 1,
        "tags": ["dsa", "linked-list", "complexity"],
        "options": [
            {"key": "A", "text": "O(1)", "is_correct": True},
            {"key": "B", "text": "O(n)", "is_correct": False},
            {"key": "C", "text": "O(log n)", "is_correct": False},
            {"key": "D", "text": "O(n^2)", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Sorting Algorithms",
        "subtopic": "Bubble Sort",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the worst-case time complexity of standard Bubble Sort?",
        "explanation": "In the worst case (reverse sorted array), Bubble Sort performs n*(n-1)/2 comparisons and swaps, resulting in O(n^2) time complexity.",
        "marks": 1,
        "tags": ["dsa", "sorting", "bubble-sort"],
        "options": [
            {"key": "A", "text": "O(n log n)", "is_correct": False},
            {"key": "B", "text": "O(n^2)", "is_correct": True},
            {"key": "C", "text": "O(n)", "is_correct": False},
            {"key": "D", "text": "O(1)", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Trees",
        "subtopic": "Binary Search Trees",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the worst-case time complexity of searching in an unbalanced Binary Search Tree (BST) with N nodes?",
        "explanation": "If elements are inserted in sorted order, an unbalanced BST degenerates into a linear linked list with height N, resulting in O(N) search time.",
        "marks": 1,
        "tags": ["dsa", "bst", "trees", "complexity"],
        "options": [
            {"key": "A", "text": "O(N)", "is_correct": True},
            {"key": "B", "text": "O(log N)", "is_correct": False},
            {"key": "C", "text": "O(1)", "is_correct": False},
            {"key": "D", "text": "O(N log N)", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Sorting Algorithms",
        "subtopic": "Merge Sort",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the auxiliary space complexity of standard top-down Merge Sort for an array of size N?",
        "explanation": "Standard top-down Merge Sort requires O(N) auxiliary space to store temporary merged sub-arrays during the merge phase.",
        "marks": 1,
        "tags": ["dsa", "merge-sort", "space-complexity"],
        "options": [
            {"key": "A", "text": "O(N)", "is_correct": True},
            {"key": "B", "text": "O(1)", "is_correct": False},
            {"key": "C", "text": "O(log N)", "is_correct": False},
            {"key": "D", "text": "O(N^2)", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Graphs",
        "subtopic": "Graph Traversal",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which data structure is fundamentally utilized to implement Breadth-First Search (BFS) on a graph?",
        "explanation": "BFS explores vertices level by level, requiring a Queue (FIFO) to track adjacent vertices in exploration order.",
        "marks": 1,
        "tags": ["dsa", "bfs", "graphs", "queue"],
        "options": [
            {"key": "A", "text": "Queue", "is_correct": True},
            {"key": "B", "text": "Stack", "is_correct": False},
            {"key": "C", "text": "Priority Queue", "is_correct": False},
            {"key": "D", "text": "Binary Heap", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Hashing",
        "subtopic": "Collision Resolution",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is Open Addressing in Hash Tables?",
        "explanation": "In Open Addressing, all entry records are stored directly within the hash table array itself. When collisions occur, probing sequences (linear, quadratic, or double hashing) find the next open slot.",
        "marks": 1,
        "tags": ["dsa", "hashing", "open-addressing"],
        "options": [
            {"key": "A", "text": "A collision resolution method where all items reside within the hash table array using probing", "is_correct": True},
            {"key": "B", "text": "Storing collided elements in external linked lists outside the table", "is_correct": False},
            {"key": "C", "text": "Re-hashing the entire table every time a collision occurs", "is_correct": False},
            {"key": "D", "text": "Discarding colliding keys automatically", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Trees",
        "subtopic": "Self-Balancing Trees",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In an AVL Tree, what is the maximum allowable difference between the heights of the left and right subtrees for any node?",
        "explanation": "An AVL tree maintains a balance factor (height(left) - height(right)) of -1, 0, or 1 for every node, rebalancing via rotations whenever the absolute difference exceeds 1.",
        "marks": 1,
        "tags": ["dsa", "avl", "self-balancing", "trees"],
        "options": [
            {"key": "A", "text": "1", "is_correct": True},
            {"key": "B", "text": "0", "is_correct": False},
            {"key": "C", "text": "2", "is_correct": False},
            {"key": "D", "text": "log N", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Graphs",
        "subtopic": "Shortest Path",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Under what condition will Dijkstra's algorithm fail to find the correct shortest path in a weighted graph?",
        "explanation": "Dijkstra's algorithm assumes that visiting a node guarantees its shortest distance has been finalized. Negative edge weights violate this greedy assumption; the Bellman-Ford algorithm must be used instead.",
        "marks": 1,
        "tags": ["dsa", "dijkstra", "graphs", "shortest-path"],
        "options": [
            {"key": "A", "text": "When the graph contains negative edge weights", "is_correct": True},
            {"key": "B", "text": "When the graph contains directed cycles with positive weights", "is_correct": False},
            {"key": "C", "text": "When the graph has more than 1,000 vertices", "is_correct": False},
            {"key": "D", "text": "When the graph is disconnected", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Dynamic Programming",
        "subtopic": "Knapsack Problem",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the time complexity of solving the 0/1 Knapsack Problem with N items and capacity W using Dynamic Programming?",
        "explanation": "The standard DP table has dimensions (N+1) x (W+1), requiring O(N * W) time (pseudo-polynomial with respect to W).",
        "marks": 1,
        "tags": ["dsa", "dynamic-programming", "knapsack"],
        "options": [
            {"key": "A", "text": "O(N * W)", "is_correct": True},
            {"key": "B", "text": "O(2^N)", "is_correct": False},
            {"key": "C", "text": "O(N log W)", "is_correct": False},
            {"key": "D", "text": "O(N + W)", "is_correct": False}
        ]
    },
    {
        "technology": "DSA",
        "topic": "Disjoint Sets",
        "subtopic": "Union-Find",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the nearly constant amortized time complexity of Union-Find operations when both Path Compression and Union by Rank are applied?",
        "explanation": "When combining Path Compression with Union by Rank, operations run in O(α(N)) amortized time, where α is the extremely slowly growing Inverse Ackermann function (effectively <= 4 for all practical universe sizes).",
        "marks": 1,
        "tags": ["dsa", "union-find", "disjoint-set", "ackermann"],
        "options": [
            {"key": "A", "text": "O(alpha(N)) where alpha is the Inverse Ackermann function", "is_correct": True},
            {"key": "B", "text": "O(log N)", "is_correct": False},
            {"key": "C", "text": "O(N)", "is_correct": False},
            {"key": "D", "text": "O(1) strict worst-case", "is_correct": False}
        ]
    },

    # =========================================================================
    # 7. REACT (12 Questions)
    # =========================================================================
    {
        "technology": "React",
        "topic": "Core Concepts",
        "subtopic": "JSX",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is JSX in React?",
        "explanation": "JSX is a syntax extension to JavaScript that allows developers to write HTML-like markup inside JavaScript files, which transpilers compile into React.createElement calls.",
        "marks": 1,
        "tags": ["react", "jsx", "syntax"],
        "options": [
            {"key": "A", "text": "A syntax extension that allows writing HTML-like markup inside JavaScript", "is_correct": True},
            {"key": "B", "text": "A CSS preprocessor built into Vite and Webpack", "is_correct": False},
            {"key": "C", "text": "A database query language for React Native", "is_correct": False},
            {"key": "D", "text": "A state management library replacing Redux", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Components & Props",
        "subtopic": "Props",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Are props in React mutable by the receiving child component?",
        "explanation": "React enforces a strict unidirectional data flow; props are read-only and immutable from the perspective of the child component.",
        "marks": 1,
        "tags": ["react", "props", "components"],
        "options": [
            {"key": "A", "text": "No, props are strictly read-only and immutable by the child", "is_correct": True},
            {"key": "B", "text": "Yes, children can modify props directly via 'this.props.val = ...'", "is_correct": False},
            {"key": "C", "text": "Only if defined as stateful props using useProps()", "is_correct": False},
            {"key": "D", "text": "Only in functional components, not class components", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "State & Hooks",
        "subtopic": "useState",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does the useState hook return in React?",
        "explanation": "useState returns a two-element array containing the current state value and an updater function to dispatch state transitions.",
        "marks": 1,
        "tags": ["react", "hooks", "usestate"],
        "options": [
            {"key": "A", "text": "An array with two elements: [currentState, setterFunction]", "is_correct": True},
            {"key": "B", "text": "An object with fields { state, setState }", "is_correct": False},
            {"key": "C", "text": "A single reactive proxy object", "is_correct": False},
            {"key": "D", "text": "A promise resolving to the next state value", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Core Concepts",
        "subtopic": "Virtual DOM",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Why does React utilize a Virtual DOM?",
        "explanation": "Manipulating the real browser DOM is slow. React compares changes in a lightweight in-memory Virtual DOM (diffing) and batches minimal real DOM updates.",
        "marks": 1,
        "tags": ["react", "virtual-dom", "performance"],
        "options": [
            {"key": "A", "text": "To batch and minimize expensive direct manipulations of the real browser DOM", "is_correct": True},
            {"key": "B", "text": "To bypass browser security sandbox restrictions", "is_correct": False},
            {"key": "C", "text": "To replace HTML with server-side WebAssembly bytecode", "is_correct": False},
            {"key": "D", "text": "To enable peer-to-peer WebRTC connections between clients", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Hooks",
        "subtopic": "useEffect",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What occurs when the dependency array of a 'useEffect' hook is omitted entirely (i.e. useEffect(() => { ... }))?",
        "explanation": "Omitting the dependency array causes the effect function to run after initial mount and after every subsequent component render.",
        "marks": 1,
        "tags": ["react", "useeffect", "lifecycle", "hooks"],
        "options": [
            {"key": "A", "text": "The effect runs after initial mount and after every single component render", "is_correct": True},
            {"key": "B", "text": "The effect runs exactly once when the component mounts", "is_correct": False},
            {"key": "C", "text": "The effect never executes unless triggered manually by an event handler", "is_correct": False},
            {"key": "D", "text": "React throws a runtime HookDependencyException", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Hooks",
        "subtopic": "useRef",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does updating 'ref.current' via useRef differ from updating state via useState?",
        "explanation": "Mutating 'ref.current' does NOT trigger a component re-render, whereas calling a useState setter schedules a re-render of the component tree.",
        "marks": 1,
        "tags": ["react", "useref", "hooks", "rendering"],
        "options": [
            {"key": "A", "text": "Mutating ref.current does not trigger a component re-render", "is_correct": True},
            {"key": "B", "text": "useRef is asynchronous, while useState is synchronous", "is_correct": False},
            {"key": "C", "text": "useRef can only store strings, while useState stores any type", "is_correct": False},
            {"key": "D", "text": "useRef values reset to null on every render", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Performance",
        "subtopic": "useMemo vs useCallback",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the primary difference between 'useMemo' and 'useCallback'?",
        "explanation": "'useMemo' caches the result of calling a calculation function, while 'useCallback' caches the function definition itself between renders.",
        "marks": 1,
        "tags": ["react", "usememo", "usecallback", "performance"],
        "options": [
            {"key": "A", "text": "useMemo memoizes the computed return value; useCallback memoizes the function definition itself", "is_correct": True},
            {"key": "B", "text": "useMemo is for class components; useCallback is for functional components", "is_correct": False},
            {"key": "C", "text": "useCallback executes asynchronously in web workers", "is_correct": False},
            {"key": "D", "text": "useMemo only accepts primitive numeric dependencies", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Context & State",
        "subtopic": "Context API",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What performance issue can arise when a high-frequency changing state is placed inside a single React Context provider?",
        "explanation": "Every component that consumes the context will re-render whenever the context value changes, even if it only relies on an unchanged property of that context.",
        "marks": 1,
        "tags": ["react", "context-api", "performance"],
        "options": [
            {"key": "A", "text": "All consuming components re-render whenever any part of the context value changes", "is_correct": True},
            {"key": "B", "text": "React crashes with an OutOfMemoryError after 100 updates", "is_correct": False},
            {"key": "C", "text": "The browser DOM freezes due to synchronous blocking WebSocket connections", "is_correct": False},
            {"key": "D", "text": "Context values cannot be updated more than once per second", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Concurrent React",
        "subtopic": "Fiber Architecture",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What architectural capability does the React Fiber reconciler provide over the legacy stack reconciler?",
        "explanation": "Fiber enables incremental rendering by splitting rendering work into small work units that can be paused, prioritized, aborted, or resumed, preventing UI lag during heavy renders.",
        "marks": 1,
        "tags": ["react", "fiber", "reconciliation", "architecture"],
        "options": [
            {"key": "A", "text": "Ability to pause, prioritize, and resume work units to keep the browser main thread responsive", "is_correct": True},
            {"key": "B", "text": "Direct compilation of JSX into GPU shader programs", "is_correct": False},
            {"key": "C", "text": "Replacement of JavaScript with statically linked C++ modules", "is_correct": False},
            {"key": "D", "text": "Elimination of all component state in favor of global browser storage", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Concurrent React",
        "subtopic": "useTransition",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary objective of the 'useTransition' hook in React 18?",
        "explanation": "'useTransition' marks state updates as non-urgent transitions, allowing urgent updates (such as typing or clicking) to interrupt and remain responsive.",
        "marks": 1,
        "tags": ["react", "usetransition", "concurrent", "react18"],
        "options": [
            {"key": "A", "text": "Marks state updates as non-urgent transitions, keeping the UI responsive to urgent user input", "is_correct": True},
            {"key": "B", "text": "Defines CSS animations between route changes", "is_correct": False},
            {"key": "C", "text": "Transfers component state across server worker threads", "is_correct": False},
            {"key": "D", "text": "Converts synchronous fetch calls into background polling loops", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Architecture",
        "subtopic": "Server Components (RSC)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is a key difference between React Server Components (RSC) and traditional Client Components?",
        "explanation": "RSCs execute strictly on the server and their code dependencies are never bundled into the client JavaScript bundle, reducing client bundle size.",
        "marks": 1,
        "tags": ["react", "rsc", "server-components"],
        "options": [
            {"key": "A", "text": "RSCs execute strictly on the server, sending zero JavaScript bundle weight for their implementation to the client", "is_correct": True},
            {"key": "B", "text": "RSCs can access browser APIs like localStorage and window directly", "is_correct": False},
            {"key": "C", "text": "RSCs can use useState and useEffect hooks without restrictions", "is_correct": False},
            {"key": "D", "text": "RSCs cannot accept props or render child components", "is_correct": False}
        ]
    },
    {
        "technology": "React",
        "topic": "Error Handling",
        "subtopic": "Error Boundaries",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Which types of errors are NOT caught by React Error Boundaries?",
        "explanation": "Error Boundaries do not catch errors inside event handlers, asynchronous code (e.g. setTimeout, fetch), server-side rendering, or errors thrown in the Error Boundary itself.",
        "marks": 1,
        "tags": ["react", "error-boundaries", "error-handling"],
        "options": [
            {"key": "A", "text": "Errors in event handlers and asynchronous callbacks (e.g. setTimeout, fetch)", "is_correct": True},
            {"key": "B", "text": "Errors during render method execution", "is_correct": False},
            {"key": "C", "text": "Errors inside lifecycle methods or constructor functions of children", "is_correct": False},
            {"key": "D", "text": "Null pointer exceptions during JSX tree creation", "is_correct": False}
        ]
    },

    # =========================================================================
    # 8. JAVASCRIPT (12 Questions)
    # =========================================================================
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Variables & Declarations",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the scope of a variable declared with 'let' or 'const' in JavaScript?",
        "explanation": "Variables declared with 'let' and 'const' have block scope (delimited by curly braces {}), unlike 'var' which has function scope.",
        "marks": 1,
        "tags": ["javascript", "let", "const", "scope"],
        "options": [
            {"key": "A", "text": "Block scope", "is_correct": True},
            {"key": "B", "text": "Function scope", "is_correct": False},
            {"key": "C", "text": "Global scope always", "is_correct": False},
            {"key": "D", "text": "Module scope only", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Type Checking",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the output of 'typeof null' in JavaScript?",
        "explanation": "Due to a historical bug in the first implementation of JavaScript, typeof null evaluates to 'object'.",
        "marks": 1,
        "tags": ["javascript", "typeof", "types"],
        "options": [
            {"key": "A", "text": "'null'", "is_correct": False},
            {"key": "B", "text": "'object'", "is_correct": True},
            {"key": "C", "text": "'undefined'", "is_correct": False},
            {"key": "D", "text": "'boolean'", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Equality Operators",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the difference between '==' and '===' in JavaScript?",
        "explanation": "'==' performs type coercion before comparison, whereas '===' (strict equality) checks both value and type without coercion.",
        "marks": 1,
        "tags": ["javascript", "equality", "coercion"],
        "options": [
            {"key": "A", "text": "'==' performs type coercion, while '===' checks both value and type strictly", "is_correct": True},
            {"key": "B", "text": "'===' is only for comparing objects, while '==' compares primitives", "is_correct": False},
            {"key": "C", "text": "'==' checks memory address, while '===' checks string length", "is_correct": False},
            {"key": "D", "text": "There is no difference in ES6+", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Arrays",
        "subtopic": "Array Methods",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which array method creates a new array populated with the results of calling a provided function on every element?",
        "explanation": "Array.prototype.map() transforms elements into a new array of the same length without mutating the original array.",
        "marks": 1,
        "tags": ["javascript", "arrays", "map"],
        "options": [
            {"key": "A", "text": "forEach()", "is_correct": False},
            {"key": "B", "text": "map()", "is_correct": True},
            {"key": "C", "text": "filter()", "is_correct": False},
            {"key": "D", "text": "reduce()", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Scope & Closures",
        "subtopic": "Closures",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is a closure in JavaScript?",
        "explanation": "A closure is the combination of a function bundled together with references to its surrounding lexical state, allowing inner functions to access outer variables even after the outer function has returned.",
        "marks": 1,
        "tags": ["javascript", "closures", "scope"],
        "options": [
            {"key": "A", "text": "A function bundled with references to its surrounding lexical environment", "is_correct": True},
            {"key": "B", "text": "A method to close open network sockets in Node.js", "is_correct": False},
            {"key": "C", "text": "A garbage collector heuristic to delete unreferenced variables", "is_correct": False},
            {"key": "D", "text": "A syntax rule requiring closing braces in ES modules", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Asynchronous Programming",
        "subtopic": "Promises",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What are the three mutually exclusive states of a JavaScript Promise?",
        "explanation": "A Promise is always in one of three states: pending (initial state), fulfilled (operation completed successfully), or rejected (operation failed).",
        "marks": 1,
        "tags": ["javascript", "promises", "async"],
        "options": [
            {"key": "A", "text": "pending, fulfilled, rejected", "is_correct": True},
            {"key": "B", "text": "waiting, executing, finished", "is_correct": False},
            {"key": "C", "text": "unresolved, resolved, error", "is_correct": False},
            {"key": "D", "text": "idle, active, closed", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Functions & Context",
        "subtopic": "'this' Keyword",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does the 'this' keyword behave inside an arrow function?",
        "explanation": "Arrow functions do not bind their own 'this'; they retain the 'this' value of the enclosing lexical context at the time they are created.",
        "marks": 1,
        "tags": ["javascript", "this", "arrow-functions"],
        "options": [
            {"key": "A", "text": "It lexically captures 'this' from the enclosing execution context", "is_correct": True},
            {"key": "B", "text": "It always points to the global window object", "is_correct": False},
            {"key": "C", "text": "It can be rebound using .bind(), .call(), or .apply()", "is_correct": False},
            {"key": "D", "text": "It is undefined in both strict and non-strict modes", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Core Language",
        "subtopic": "Hoisting",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What occurs when accessing a 'let' variable before its declaration line (Temporal Dead Zone)?",
        "explanation": "'let' and 'const' variables are hoisted but remain uninitialized in the Temporal Dead Zone (TDZ). Accessing them before initialization throws a ReferenceError.",
        "marks": 1,
        "tags": ["javascript", "hoisting", "tdz", "reference-error"],
        "options": [
            {"key": "A", "text": "A ReferenceError is thrown", "is_correct": True},
            {"key": "B", "text": "The variable evaluates to undefined", "is_correct": False},
            {"key": "C", "text": "The variable evaluates to null", "is_correct": False},
            {"key": "D", "text": "The code executes silently without error", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Event Loop",
        "subtopic": "Microtasks vs Macrotasks",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In the JavaScript Event Loop, when are microtasks (e.g. Promise callbacks, queueMicrotask) executed relative to macrotasks (e.g. setTimeout)?",
        "explanation": "All queued microtasks are completely drained at the end of the current task before the browser yields to the next macrotask or rendering phase.",
        "marks": 1,
        "tags": ["javascript", "event-loop", "microtasks", "macrotasks"],
        "options": [
            {"key": "A", "text": "Microtasks run immediately after the current task finishes, before the next macrotask or rendering", "is_correct": True},
            {"key": "B", "text": "Macrotasks always preempt microtasks", "is_correct": False},
            {"key": "C", "text": "Microtasks execute once every 16ms during requestAnimationFrame", "is_correct": False},
            {"key": "D", "text": "Microtasks and macrotasks are interleaved in a 1:1 round-robin fashion", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Prototypes",
        "subtopic": "Prototypal Inheritance",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the terminal node at the end of the prototype chain for normal JavaScript objects?",
        "explanation": "Normal objects inherit from Object.prototype, whose internal [[Prototype]] is null, terminating the prototype lookup chain.",
        "marks": 1,
        "tags": ["javascript", "prototypes", "inheritance"],
        "options": [
            {"key": "A", "text": "null (via Object.prototype.__proto__)", "is_correct": True},
            {"key": "B", "text": "undefined", "is_correct": False},
            {"key": "C", "text": "Function.prototype", "is_correct": False},
            {"key": "D", "text": "globalThis", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Metaprogramming",
        "subtopic": "Proxy & Reflect",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary role of the Proxy object in JavaScript?",
        "explanation": "The Proxy object enables you to create an object that wraps another object (target) and intercepts fundamental operations like property lookup, assignment, enumeration, and function invocation.",
        "marks": 1,
        "tags": ["javascript", "proxy", "reflect", "metaprogramming"],
        "options": [
            {"key": "A", "text": "To intercept and customize fundamental operations (get, set, apply) on a target object", "is_correct": True},
            {"key": "B", "text": "To establish an HTTP forward proxy tunnel for fetch requests", "is_correct": False},
            {"key": "C", "text": "To compress JavaScript source code in memory", "is_correct": False},
            {"key": "D", "text": "To encrypt object properties using TLS 1.3", "is_correct": False}
        ]
    },
    {
        "technology": "JavaScript",
        "topic": "Memory & Optimization",
        "subtopic": "WeakMap & WeakSet",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why do WeakMap and WeakSet prevent memory leaks compared to standard Map and Set in JavaScript?",
        "explanation": "Keys in a WeakMap are held weakly; if there are no other references to a key object, it can be garbage collected even if present in the WeakMap.",
        "marks": 1,
        "tags": ["javascript", "weakmap", "garbage-collection", "memory"],
        "options": [
            {"key": "A", "text": "Keys are held as weak references, allowing them to be garbage collected when unreferenced elsewhere", "is_correct": True},
            {"key": "B", "text": "They store data on disk rather than RAM", "is_correct": False},
            {"key": "C", "text": "They automatically delete entries after a 5-minute timeout", "is_correct": False},
            {"key": "D", "text": "They only accept primitive numbers as keys", "is_correct": False}
        ]
    },

    # =========================================================================
    # 9. HTML (12 Questions)
    # =========================================================================
    {
        "technology": "HTML",
        "topic": "Semantic HTML",
        "subtopic": "Structural Tags",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which semantic HTML5 tag represents introductory or navigational content for a page or section?",
        "explanation": "The '<header>' tag represents a container for introductory content or a set of navigational links.",
        "marks": 1,
        "tags": ["html", "semantic-html", "header"],
        "options": [
            {"key": "A", "text": "<top>", "is_correct": False},
            {"key": "B", "text": "<header>", "is_correct": True},
            {"key": "C", "text": "<head>", "is_correct": False},
            {"key": "D", "text": "<intro>", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Forms & Inputs",
        "subtopic": "Input Types",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which HTML input type provides built-in browser-level email address format validation?",
        "explanation": "<input type='email'> causes the browser to validate that the entered text matches standard email syntax before form submission.",
        "marks": 1,
        "tags": ["html", "forms", "validation", "email"],
        "options": [
            {"key": "A", "text": "type='mail'", "is_correct": False},
            {"key": "B", "text": "type='email'", "is_correct": True},
            {"key": "C", "text": "type='address'", "is_correct": False},
            {"key": "D", "text": "type='text' validate='email'", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Media",
        "subtopic": "Images & Accessibility",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the purpose of the 'alt' attribute on an <img> tag in HTML?",
        "explanation": "The 'alt' attribute provides an alternative text description rendered when the image fails to load and read aloud by screen readers for accessibility.",
        "marks": 1,
        "tags": ["html", "images", "accessibility", "alt"],
        "options": [
            {"key": "A", "text": "Provides alternative text for screen readers and displays when the image fails to load", "is_correct": True},
            {"key": "B", "text": "Specifies a secondary URL fallback if the first image times out", "is_correct": False},
            {"key": "C", "text": "Alters the CSS aspect ratio of the image", "is_correct": False},
            {"key": "D", "text": "Defines tooltip hover text in all browsers", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Document Structure",
        "subtopic": "Doctype",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does the '<!DOCTYPE html>' declaration at the beginning of an HTML file do?",
        "explanation": "'<!DOCTYPE html>' informs the browser that the document is written in HTML5, triggering standards mode rendering instead of quirks mode.",
        "marks": 1,
        "tags": ["html", "doctype", "standards"],
        "options": [
            {"key": "A", "text": "Informs the browser to render the page in HTML5 standards mode", "is_correct": True},
            {"key": "B", "text": "Imports external HTML modules from W3C CDN", "is_correct": False},
            {"key": "C", "text": "Enforces strict XHTML XML parsing validation", "is_correct": False},
            {"key": "D", "text": "Enables server-side rendering in Apache and NGINX", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Accessibility",
        "subtopic": "ARIA & Roles",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the First Rule of ARIA use according to W3C accessibility guidelines?",
        "explanation": "If you can use a native HTML element or attribute with the semantics and behavior you require already built in, do so instead of re-purposing an element and adding ARIA.",
        "marks": 1,
        "tags": ["html", "accessibility", "aria", "w3c"],
        "options": [
            {"key": "A", "text": "Use native semantic HTML elements whenever available before falling back to ARIA", "is_correct": True},
            {"key": "B", "text": "Always add role='button' to every clickable <div> or <span>", "is_correct": False},
            {"key": "C", "text": "ARIA attributes must only be declared via JavaScript, never static HTML", "is_correct": False},
            {"key": "D", "text": "Screen readers must be disabled on mobile responsive layouts", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Performance & Loading",
        "subtopic": "Script Loading Attributes",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does '<script defer>' differ from '<script async>' in HTML?",
        "explanation": "'defer' scripts download in parallel with HTML parsing and execute in document order only after HTML parsing is complete. 'async' scripts download in parallel and execute immediately upon completion, pausing parsing.",
        "marks": 1,
        "tags": ["html", "performance", "scripts", "defer", "async"],
        "options": [
            {"key": "A", "text": "'defer' preserves document execution order and runs after parsing; 'async' executes immediately when downloaded", "is_correct": True},
            {"key": "B", "text": "'async' preserves script order, while 'defer' executes scripts randomly", "is_correct": False},
            {"key": "C", "text": "'defer' only works for inline scripts, not external files", "is_correct": False},
            {"key": "D", "text": "There is no difference; 'defer' is an obsolete IE6 attribute", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Forms",
        "subtopic": "Labels & Inputs",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How do you programmatically associate a <label> with an <input> element?",
        "explanation": "By setting the label's 'for' attribute to match the input element's 'id' attribute (or by nesting the input inside the label).",
        "marks": 1,
        "tags": ["html", "forms", "accessibility", "labels"],
        "options": [
            {"key": "A", "text": "By matching the label's 'for' attribute with the input's 'id'", "is_correct": True},
            {"key": "B", "text": "By setting the input's 'name' equal to the label's 'class'", "is_correct": False},
            {"key": "C", "text": "By assigning them identical 'role' attributes", "is_correct": False},
            {"key": "D", "text": "HTML automatically links labels to the next sibling input", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Media",
        "subtopic": "Responsive Images",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the purpose of the <picture> element and its child <source> elements in HTML5?",
        "explanation": "The <picture> element allows developers to specify multiple image sources tailored for different screen densities, media queries, and modern formats (e.g. WebP, AVIF) with art direction.",
        "marks": 1,
        "tags": ["html", "responsive", "images", "picture"],
        "options": [
            {"key": "A", "text": "To serve different image resolutions, formats, and aspect ratios based on media queries", "is_correct": True},
            {"key": "B", "text": "To animate multiple JPEG frames like a GIF", "is_correct": False},
            {"key": "C", "text": "To capture webcam frames directly without JavaScript", "is_correct": False},
            {"key": "D", "text": "To encrypt images before transmitting them over HTTP", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Security",
        "subtopic": "Content Security Policy (CSP)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How can a web developer enforce a Content Security Policy (CSP) via HTML without server HTTP header access?",
        "explanation": "A CSP can be declared inside the HTML document using a <meta http-equiv='Content-Security-Policy' content='...'> element inside the <head>.",
        "marks": 1,
        "tags": ["html", "security", "csp"],
        "options": [
            {"key": "A", "text": "Using a <meta http-equiv='Content-Security-Policy' content='...'> tag in the <head>", "is_correct": True},
            {"key": "B", "text": "By declaring '<!DOCTYPE html csp='strict'>'", "is_correct": False},
            {"key": "C", "text": "Using an inline <script csp='true'> block", "is_correct": False},
            {"key": "D", "text": "CSP cannot be defined in HTML; it is strictly an operating system setting", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Security",
        "subtopic": "target='_blank' Vulnerability",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why is it important to add 'rel=\"noopener noreferrer\"' to external links with target='_blank'?",
        "explanation": "Without 'noopener', the newly opened page gains access to the opening window via 'window.opener', potentially allowing malicious sites to redirect the original tab to a phishing site (reverse tabnabbing).",
        "marks": 1,
        "tags": ["html", "security", "tabnabbing", "noopener"],
        "options": [
            {"key": "A", "text": "To prevent the target page from accessing window.opener and performing reverse tabnabbing attacks", "is_correct": True},
            {"key": "B", "text": "To prevent search engines from indexing the target URL", "is_correct": False},
            {"key": "C", "text": "To force the browser to download the link rather than navigate", "is_correct": False},
            {"key": "D", "text": "To encrypt the outgoing HTTP Referer header with TLS", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Web Components",
        "subtopic": "Shadow DOM",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What capability does the Shadow DOM provide in HTML Web Components?",
        "explanation": "Shadow DOM provides true DOM and CSS style scoping, isolating component internals so global styles do not leak in and component styles do not leak out.",
        "marks": 1,
        "tags": ["html", "web-components", "shadow-dom"],
        "options": [
            {"key": "A", "text": "Encapsulates a scoped DOM tree and isolated CSS styles that do not clash with the main document", "is_correct": True},
            {"key": "B", "text": "Renders components in a separate headless Chromium process", "is_correct": False},
            {"key": "C", "text": "Renders 3D graphics on a canvas background", "is_correct": False},
            {"key": "D", "text": "Replaces the browser DOM with an SQLite in-memory database", "is_correct": False}
        ]
    },
    {
        "technology": "HTML",
        "topic": "Performance",
        "subtopic": "Resource Hints",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the difference between '<link rel=\"preload\">' and '<link rel=\"prefetch\">'?",
        "explanation": "'preload' is a mandatory, high-priority request for a resource needed for the current navigation. 'prefetch' is a low-priority request for a resource likely to be needed on a future navigation.",
        "marks": 1,
        "tags": ["html", "performance", "preload", "prefetch"],
        "options": [
            {"key": "A", "text": "'preload' fetches critical resources for the current page; 'prefetch' downloads resources for anticipated future navigations", "is_correct": True},
            {"key": "B", "text": "'prefetch' blocks rendering, while 'preload' is non-blocking", "is_correct": False},
            {"key": "C", "text": "'preload' is only for fonts, while 'prefetch' is exclusively for CSS", "is_correct": False},
            {"key": "D", "text": "'preload' stores files in localStorage; 'prefetch' stores in cookies", "is_correct": False}
        ]
    },

    # =========================================================================
    # 10. CSS (12 Questions)
    # =========================================================================
    {
        "technology": "CSS",
        "topic": "Box Model",
        "subtopic": "box-sizing",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What does 'box-sizing: border-box;' do to an element's dimensions?",
        "explanation": "With border-box, padding and border are included within the element's specified width and height, preventing layout expansion.",
        "marks": 1,
        "tags": ["css", "box-model", "border-box"],
        "options": [
            {"key": "A", "text": "Padding and border widths are included within the element's specified width and height", "is_correct": True},
            {"key": "B", "text": "Margins are added inside the background color", "is_correct": False},
            {"key": "C", "text": "It removes all borders and outlines from the element", "is_correct": False},
            {"key": "D", "text": "It forces the element to display as an inline block", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Selectors",
        "subtopic": "Specificity",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which CSS selector has the highest specificity among the following options?",
        "explanation": "ID selectors (#id) have specificity (1, 0, 0), which outweighs class selectors (.class, 0, 1, 0) and element selectors (tag, 0, 0, 1).",
        "marks": 1,
        "tags": ["css", "selectors", "specificity"],
        "options": [
            {"key": "A", "text": "div p", "is_correct": False},
            {"key": "B", "text": ".container .button", "is_correct": False},
            {"key": "C", "text": "#main-header", "is_correct": True},
            {"key": "D", "text": "* (universal selector)", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Positioning",
        "subtopic": "Position Values",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How does 'position: absolute;' position an element?",
        "explanation": "'position: absolute' positions an element relative to its nearest non-static positioned ancestor (or the initial containing block if none).",
        "marks": 1,
        "tags": ["css", "position", "layout"],
        "options": [
            {"key": "A", "text": "Relative to its nearest non-static positioned ancestor", "is_correct": True},
            {"key": "B", "text": "Always relative to the browser viewport, fixed during scrolling", "is_correct": False},
            {"key": "C", "text": "Directly following its previous sibling in normal document flow", "is_correct": False},
            {"key": "D", "text": "Centered automatically in both horizontal and vertical axes", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Colors & Units",
        "subtopic": "Relative Units",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the base reference for the 'rem' CSS unit?",
        "explanation": "The 'rem' (root em) unit is relative to the font-size of the root <html> element, preventing compound cascading scaling issues caused by 'em'.",
        "marks": 1,
        "tags": ["css", "units", "rem"],
        "options": [
            {"key": "A", "text": "The font-size of the root <html> element", "is_correct": True},
            {"key": "B", "text": "The font-size of the immediate parent element", "is_correct": False},
            {"key": "C", "text": "The width of the device screen in millimeters", "is_correct": False},
            {"key": "D", "text": "1% of the viewport height", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Flexbox",
        "subtopic": "Alignment",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which CSS Flexbox property aligns items along the cross axis?",
        "explanation": "'align-items' controls alignment along the cross axis, while 'justify-content' aligns items along the main axis.",
        "marks": 1,
        "tags": ["css", "flexbox", "align-items"],
        "options": [
            {"key": "A", "text": "justify-content", "is_correct": False},
            {"key": "B", "text": "align-items", "is_correct": True},
            {"key": "C", "text": "flex-direction", "is_correct": False},
            {"key": "D", "text": "flex-wrap", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "CSS Grid",
        "subtopic": "fr Unit",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does 'grid-template-columns: 1fr 2fr;' represent in CSS Grid?",
        "explanation": "The 'fr' unit represents a fraction of free available space in the grid container. '1fr 2fr' splits available space into 3 parts, allocating 1/3 to column 1 and 2/3 to column 2.",
        "marks": 1,
        "tags": ["css", "grid", "fr-unit"],
        "options": [
            {"key": "A", "text": "Column 2 receives twice as much of the available free space as column 1", "is_correct": True},
            {"key": "B", "text": "Column 1 is fixed at 100px, and column 2 is fixed at 200px", "is_correct": False},
            {"key": "C", "text": "Column 1 renders in the foreground; column 2 renders in the background", "is_correct": False},
            {"key": "D", "text": "It creates a grid with 1 row and 2 columns of equal fixed width", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Responsive Design",
        "subtopic": "Media Queries",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the Mobile-First responsive CSS design approach?",
        "explanation": "Mobile-First writes base CSS styles for mobile viewports without media queries, then progressively enhances layout for larger screens using min-width media queries.",
        "marks": 1,
        "tags": ["css", "mobile-first", "responsive"],
        "options": [
            {"key": "A", "text": "Designing for small screens first and progressively enhancing via min-width queries", "is_correct": True},
            {"key": "B", "text": "Hiding all desktop components on mobile devices using display: none", "is_correct": False},
            {"key": "C", "text": "Using max-width queries starting from 4K resolution downward", "is_correct": False},
            {"key": "D", "text": "Serving entirely different HTML files based on user-agent strings", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Selectors",
        "subtopic": "Pseudo-classes",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which CSS pseudo-class matches an element only if it has NO children (including text nodes)?",
        "explanation": "The ':empty' pseudo-class represents any element that has no children whatsoever, including white-space text nodes.",
        "marks": 1,
        "tags": ["css", "selectors", "pseudo-classes"],
        "options": [
            {"key": "A", "text": ":empty", "is_correct": True},
            {"key": "B", "text": ":blank", "is_correct": False},
            {"key": "C", "text": ":void", "is_correct": False},
            {"key": "D", "text": ":null", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Performance & Rendering",
        "subtopic": "Composite Layering",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Which CSS properties can be animated using the GPU compositor without triggering Layout or Repaint phases?",
        "explanation": "Animating 'transform' and 'opacity' can be handled purely by the GPU compositor layer without triggering browser layout reflow or repainting.",
        "marks": 1,
        "tags": ["css", "performance", "gpu", "animation"],
        "options": [
            {"key": "A", "text": "transform and opacity", "is_correct": True},
            {"key": "B", "text": "width and height", "is_correct": False},
            {"key": "C", "text": "top and left", "is_correct": False},
            {"key": "D", "text": "margin and padding", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Modern CSS",
        "subtopic": "CSS Variables",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What distinguishes native CSS Custom Properties (CSS variables) from preprocessor variables (Sass/LESS)?",
        "explanation": "CSS Custom Properties are live in the browser DOM, cascade down the element tree, and can be dynamically read and updated via JavaScript at runtime.",
        "marks": 1,
        "tags": ["css", "custom-properties", "variables"],
        "options": [
            {"key": "A", "text": "They cascade in the DOM and can be dynamically inspected and mutated via JavaScript at runtime", "is_correct": True},
            {"key": "B", "text": "They are resolved strictly at build time and cannot change after page load", "is_correct": False},
            {"key": "C", "text": "They can only hold numeric pixel values", "is_correct": False},
            {"key": "D", "text": "They require a Node.js compiler plugin to execute", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Layout Architecture",
        "subtopic": "BFC (Block Formatting Context)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Which of the following creates a new Block Formatting Context (BFC) on an element?",
        "explanation": "Properties such as 'overflow: hidden' (or any value other than visible), 'display: flow-root', 'position: absolute/fixed', and 'display: flex' create a BFC, containing internal floats and preventing margin collapsing.",
        "marks": 1,
        "tags": ["css", "bfc", "layout"],
        "options": [
            {"key": "A", "text": "display: flow-root or overflow: hidden", "is_correct": True},
            {"key": "B", "text": "margin: 0 auto", "is_correct": False},
            {"key": "C", "text": "color: red", "is_correct": False},
            {"key": "D", "text": "text-align: center", "is_correct": False}
        ]
    },
    {
        "technology": "CSS",
        "topic": "Modern Selectors",
        "subtopic": ":has() Pseudo-class",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why is the ':has()' selector often described as the 'parent selector' in CSS?",
        "explanation": "The ':has()' functional pseudo-class allows styling a parent or preceding sibling based on whether it contains or is followed by matching descendants (e.g. 'article:has(img)').",
        "marks": 1,
        "tags": ["css", "selectors", "has-selector"],
        "options": [
            {"key": "A", "text": "It allows styling an element based on the presence of specific descendants or siblings", "is_correct": True},
            {"key": "B", "text": "It forces child elements to inherit properties from grandparents", "is_correct": False},
            {"key": "C", "text": "It is an alias for parentElement in vanilla JavaScript", "is_correct": False},
            {"key": "D", "text": "It converts CSS Grid tracks into flex items", "is_correct": False}
        ]
    },

    # =========================================================================
    # 11. OPERATING SYSTEMS (12 Questions)
    # =========================================================================
    {
        "technology": "Operating Systems",
        "topic": "Processes & Threads",
        "subtopic": "Process vs Thread",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the primary difference between a process and a thread in modern operating systems?",
        "explanation": "A process has its own independent virtual address space and system resources, whereas threads within the same process share that memory space while maintaining their own registers and stack.",
        "marks": 1,
        "tags": ["os", "processes", "threads"],
        "options": [
            {"key": "A", "text": "Processes have isolated address spaces; threads within a process share the same address space", "is_correct": True},
            {"key": "B", "text": "Threads are managed by hardware, while processes are managed by compilers", "is_correct": False},
            {"key": "C", "text": "Processes cannot perform disk I/O, while threads can", "is_correct": False},
            {"key": "D", "text": "A thread can contain multiple child processes", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "CPU Scheduling",
        "subtopic": "Scheduling Algorithms",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which CPU scheduling algorithm allocates a fixed time quantum per process in a circular queue?",
        "explanation": "Round Robin (RR) scheduling assigns a fixed time quantum to each ready process in cyclic order, designed for time-sharing systems.",
        "marks": 1,
        "tags": ["os", "scheduling", "round-robin"],
        "options": [
            {"key": "A", "text": "First-Come, First-Served (FCFS)", "is_correct": False},
            {"key": "B", "text": "Round Robin (RR)", "is_correct": True},
            {"key": "C", "text": "Shortest Job First (SJF)", "is_correct": False},
            {"key": "D", "text": "Priority Scheduling", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "System Calls",
        "subtopic": "Kernel vs User Mode",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Why do modern operating systems operate in dual modes (User Mode vs Kernel Mode)?",
        "explanation": "Dual-mode operation prevents rogue or faulty user applications from directly modifying hardware, kernel memory, or halting the system.",
        "marks": 1,
        "tags": ["os", "kernel-mode", "protection", "security"],
        "options": [
            {"key": "A", "text": "To protect system hardware and critical kernel memory from unauthorized user application tampering", "is_correct": True},
            {"key": "B", "text": "To double CPU clock frequency during background tasks", "is_correct": False},
            {"key": "C", "text": "To allow multiple operating systems to run concurrently without virtualization", "is_correct": False},
            {"key": "D", "text": "To compress executable binaries before execution", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Memory Management",
        "subtopic": "Virtual Memory",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the primary purpose of Virtual Memory in operating systems?",
        "explanation": "Virtual memory maps process address spaces to physical RAM and secondary disk storage, allowing execution of processes larger than physical RAM while providing address isolation.",
        "marks": 1,
        "tags": ["os", "virtual-memory", "memory"],
        "options": [
            {"key": "A", "text": "To allow processes to exceed physical RAM capacity and provide memory isolation between processes", "is_correct": True},
            {"key": "B", "text": "To increase CPU register count dynamically", "is_correct": False},
            {"key": "C", "text": "To eliminate the need for hard disk storage", "is_correct": False},
            {"key": "D", "text": "To encrypt RAM data against physical bus sniffing", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Synchronization",
        "subtopic": "Semaphores & Mutexes",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the fundamental difference between a Binary Semaphore and a Mutex?",
        "explanation": "A Mutex enforces ownership (only the thread that locked it may unlock it). A Binary Semaphore has no ownership concept; one thread can signal (V) a semaphore locked by another.",
        "marks": 1,
        "tags": ["os", "synchronization", "mutex", "semaphore"],
        "options": [
            {"key": "A", "text": "A Mutex incorporates ownership (only the locking thread can unlock); semaphores have no ownership", "is_correct": True},
            {"key": "B", "text": "A Mutex can take integer values up to 256; a semaphore is strictly 0 or 1", "is_correct": False},
            {"key": "C", "text": "Semaphores are implemented strictly in user-space without kernel system calls", "is_correct": False},
            {"key": "D", "text": "Mutexes cannot prevent race conditions", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Deadlocks",
        "subtopic": "Coffman Conditions",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which of the following is NOT one of the four Coffman conditions necessary for a Deadlock?",
        "explanation": "The four Coffman conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Preemptive Multitasking prevents deadlocks rather than causing them.",
        "marks": 1,
        "tags": ["os", "deadlocks", "coffman"],
        "options": [
            {"key": "A", "text": "Mutual Exclusion", "is_correct": False},
            {"key": "B", "text": "Hold and Wait", "is_correct": False},
            {"key": "C", "text": "Preemptive Multitasking", "is_correct": True},
            {"key": "D", "text": "Circular Wait", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Memory Management",
        "subtopic": "Page Faults",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is a Page Fault in an operating system?",
        "explanation": "A page fault is an interrupt generated by the Memory Management Unit (MMU) when a program accesses a virtual memory page that is not currently mapped into physical RAM.",
        "marks": 1,
        "tags": ["os", "paging", "page-fault", "virtual-memory"],
        "options": [
            {"key": "A", "text": "A hardware trap triggered when an accessed virtual page is not currently in physical RAM", "is_correct": True},
            {"key": "B", "text": "A fatal operating system crash requiring immediate reboot", "is_correct": False},
            {"key": "C", "text": "A corrupt sector error detected on a mechanical hard drive", "is_correct": False},
            {"key": "D", "text": "An illegal instruction executed by the CPU arithmetic unit", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Inter-Process Communication",
        "subtopic": "IPC Mechanisms",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Which IPC mechanism provides the highest throughput for exchanging data between two local processes?",
        "explanation": "Shared Memory is the fastest IPC mechanism because processes read and write directly to mapped physical memory pages without copying data into kernel space.",
        "marks": 1,
        "tags": ["os", "ipc", "shared-memory", "performance"],
        "options": [
            {"key": "A", "text": "Shared Memory", "is_correct": True},
            {"key": "B", "text": "UNIX Domain Sockets", "is_correct": False},
            {"key": "C", "text": "Named Pipes (FIFOs)", "is_correct": False},
            {"key": "D", "text": "Message Queues", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Deadlocks",
        "subtopic": "Banker's Algorithm",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary role of Dijkstra's Banker's Algorithm in operating systems?",
        "explanation": "The Banker's Algorithm is a deadlock avoidance algorithm that tests for safety by simulating the allocation of predetermined maximum possible resources before granting resource requests.",
        "marks": 1,
        "tags": ["os", "bankers-algorithm", "deadlock-avoidance"],
        "options": [
            {"key": "A", "text": "Deadlock avoidance by evaluating whether granting a resource leaves the system in a safe state", "is_correct": True},
            {"key": "B", "text": "Optimizing disk read/write throughput using elevator scheduling", "is_correct": False},
            {"key": "C", "text": "Balancing network packets across multiple physical NIC interfaces", "is_correct": False},
            {"key": "D", "text": "Allocating physical heap memory pages in user-space", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Memory Management",
        "subtopic": "Thrashing",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is 'Thrashing' in an operating system with demand paging?",
        "explanation": "Thrashing occurs when the total working set size of active processes exceeds physical RAM, causing the system to spend more time swapping pages between disk and RAM than executing user instructions.",
        "marks": 1,
        "tags": ["os", "thrashing", "paging", "memory"],
        "options": [
            {"key": "A", "text": "A state where the system spends virtually all its time swapping pages rather than executing instructions", "is_correct": True},
            {"key": "B", "text": "Excessive CPU cache invalidation caused by high clock frequency", "is_correct": False},
            {"key": "C", "text": "Hardware destruction of hard disk platters due to continuous head parking", "is_correct": False},
            {"key": "D", "text": "An overflow of the kernel interrupt vector table", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "File Systems",
        "subtopic": "Inodes",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In UNIX file systems, what metadata is stored in an Inode?",
        "explanation": "An inode stores file permissions, owner/group UID, file size, timestamps, and pointers to disk data blocks, but does NOT store the file's name (stored in directory entries).",
        "marks": 1,
        "tags": ["os", "file-systems", "inode", "unix"],
        "options": [
            {"key": "A", "text": "File size, permissions, owner, timestamps, and block pointers, but NOT the file name", "is_correct": True},
            {"key": "B", "text": "The file name and full directory path only", "is_correct": False},
            {"key": "C", "text": "The decrypted contents of the file's first 4KB data sector", "is_correct": False},
            {"key": "D", "text": "The user's password hash and session tokens", "is_correct": False}
        ]
    },
    {
        "technology": "Operating Systems",
        "topic": "Hardware & Architecture",
        "subtopic": "TLB (Translation Lookaside Buffer)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the purpose of the Translation Lookaside Buffer (TLB) in CPU memory management?",
        "explanation": "The TLB is a high-speed associative hardware cache inside the CPU that caches recent virtual-to-physical page table translations, avoiding multiple RAM lookups for page tables.",
        "marks": 1,
        "tags": ["os", "tlb", "mmu", "hardware"],
        "options": [
            {"key": "A", "text": "A hardware cache that stores recent virtual-to-physical address translations to accelerate memory access", "is_correct": True},
            {"key": "B", "text": "A FIFO queue for buffering network packet reception", "is_correct": False},
            {"key": "C", "text": "A dedicated processor for executing graphics rendering pipelines", "is_correct": False},
            {"key": "D", "text": "An EEPROM chip storing system BIOS credentials", "is_correct": False}
        ]
    },

    # =========================================================================
    # 12. COMPUTER NETWORKS (12 Questions)
    # =========================================================================
    {
        "technology": "Computer Networks",
        "topic": "Network Models",
        "subtopic": "OSI Layers",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How many layers are in the ISO/OSI Reference Model?",
        "explanation": "The OSI model consists of 7 layers: Physical, Data Link, Network, Transport, Session, Presentation, and Application.",
        "marks": 1,
        "tags": ["networking", "osi-model", "layers"],
        "options": [
            {"key": "A", "text": "4", "is_correct": False},
            {"key": "B", "text": "5", "is_correct": False},
            {"key": "C", "text": "7", "is_correct": True},
            {"key": "D", "text": "9", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Transport Layer",
        "subtopic": "TCP vs UDP",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Which characteristic distinguishes UDP from TCP?",
        "explanation": "UDP is connectionless and provides no delivery guarantees, retransmissions, or flow control, yielding lower latency suitable for streaming and gaming.",
        "marks": 1,
        "tags": ["networking", "tcp", "udp", "transport"],
        "options": [
            {"key": "A", "text": "UDP is connectionless and provides no delivery or ordering guarantees", "is_correct": True},
            {"key": "B", "text": "UDP encrypts packets using hardware certificates", "is_correct": False},
            {"key": "C", "text": "UDP establishes a 3-way handshake before sending data", "is_correct": False},
            {"key": "D", "text": "UDP cannot transmit over IPv6 networks", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Application Layer",
        "subtopic": "DNS",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is the primary function of the Domain Name System (DNS)?",
        "explanation": "DNS translates human-readable hostnames (e.g. skillsphere.com) into machine-routable IP addresses (e.g. 192.0.2.1).",
        "marks": 1,
        "tags": ["networking", "dns", "ip"],
        "options": [
            {"key": "A", "text": "Translating human-readable domain names into IP addresses", "is_correct": True},
            {"key": "B", "text": "Assigning MAC addresses to physical network interface cards", "is_correct": False},
            {"key": "C", "text": "Routing packets across BGP autonomous systems", "is_correct": False},
            {"key": "D", "text": "Encrypting browser cookies over HTTPS", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Network Layer",
        "subtopic": "IP Addressing",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "How many bits are in an IPv4 address versus an IPv6 address?",
        "explanation": "An IPv4 address is 32 bits (4 bytes); an IPv6 address is 128 bits (16 bytes).",
        "marks": 1,
        "tags": ["networking", "ipv4", "ipv6", "addressing"],
        "options": [
            {"key": "A", "text": "IPv4 is 32 bits; IPv6 is 128 bits", "is_correct": True},
            {"key": "B", "text": "IPv4 is 64 bits; IPv6 is 256 bits", "is_correct": False},
            {"key": "C", "text": "IPv4 is 16 bits; IPv6 is 64 bits", "is_correct": False},
            {"key": "D", "text": "Both use 128 bits with different header formats", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Transport Layer",
        "subtopic": "TCP Handshake",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What sequence of packets establishes a standard TCP connection (3-way handshake)?",
        "explanation": "The client sends a SYN packet, the server responds with SYN-ACK, and the client replies with ACK to establish the connection.",
        "marks": 1,
        "tags": ["networking", "tcp", "handshake"],
        "options": [
            {"key": "A", "text": "SYN -> SYN-ACK -> ACK", "is_correct": True},
            {"key": "B", "text": "ACK -> SYN -> SYN-ACK", "is_correct": False},
            {"key": "C", "text": "FIN -> ACK -> FIN-ACK", "is_correct": False},
            {"key": "D", "text": "PING -> PONG -> ACK", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Application Layer",
        "subtopic": "HTTP Status Codes",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What does HTTP status code 403 Forbidden indicate compared to 401 Unauthorized?",
        "explanation": "401 indicates that authentication is missing or invalid. 403 means the client's identity is authenticated, but they lack authorization permission to access the resource.",
        "marks": 1,
        "tags": ["networking", "http", "status-codes", "security"],
        "options": [
            {"key": "A", "text": "401 means unauthenticated (login required); 403 means authenticated but unauthorized (forbidden)", "is_correct": True},
            {"key": "B", "text": "403 means the server has crashed; 401 means the page does not exist", "is_correct": False},
            {"key": "C", "text": "403 is for GET requests; 401 is strictly for POST requests", "is_correct": False},
            {"key": "D", "text": "They are synonymous aliases in HTTP/1.1", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Data Link Layer",
        "subtopic": "ARP",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the purpose of the Address Resolution Protocol (ARP)?",
        "explanation": "ARP maps a known network-layer IP address to a physical data-link MAC address on a local broadcast network segment.",
        "marks": 1,
        "tags": ["networking", "arp", "mac", "ip"],
        "options": [
            {"key": "A", "text": "Resolving an IP address to a physical MAC address on a local network segment", "is_correct": True},
            {"key": "B", "text": "Translating domain names into IPv6 addresses", "is_correct": False},
            {"key": "C", "text": "Allocating dynamic IP addresses via DHCP leases", "is_correct": False},
            {"key": "D", "text": "Encrypting Wi-Fi traffic using WPA3 protocols", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Transport Layer",
        "subtopic": "Flow Control",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "How does TCP implement Flow Control to prevent overwhelming the receiving host?",
        "explanation": "TCP implements flow control using a sliding Receive Window (rwnd) advertised in TCP segment headers, indicating how much buffer space the receiver has available.",
        "marks": 1,
        "tags": ["networking", "tcp", "flow-control", "sliding-window"],
        "options": [
            {"key": "A", "text": "Using a sliding window where the receiver advertises its available buffer size (rwnd)", "is_correct": True},
            {"key": "B", "text": "By dropping all packets that exceed 1500 bytes MTU", "is_correct": False},
            {"key": "C", "text": "By terminating the socket connection whenever the receiver buffer reaches 80%", "is_correct": False},
            {"key": "D", "text": "By executing a binary search on network bandwidth", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Transport Layer",
        "subtopic": "Congestion Control",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In TCP Congestion Control, what initiates the transition from Slow Start to Congestion Avoidance?",
        "explanation": "The sender transitions from exponential Slow Start to linear Congestion Avoidance once the congestion window (cwnd) reaches the slow-start threshold (ssthresh).",
        "marks": 1,
        "tags": ["networking", "tcp", "congestion-control", "slow-start"],
        "options": [
            {"key": "A", "text": "When the congestion window (cwnd) reaches or exceeds ssthresh", "is_correct": True},
            {"key": "B", "text": "When the receiver sends three duplicate ACK packets", "is_correct": False},
            {"key": "C", "text": "When the retransmission timer expires", "is_correct": False},
            {"key": "D", "text": "When the router sends an ICMP Source Quench message", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Security & Encryption",
        "subtopic": "TLS Handshake",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary advantage of TLS 1.3 over TLS 1.2 during connection establishment?",
        "explanation": "TLS 1.3 shortens the handshake latency from two round-trips (2-RTT) to one round-trip (1-RTT), and supports 0-RTT resumption while removing insecure legacy cryptographic ciphers.",
        "marks": 1,
        "tags": ["networking", "tls", "security", "encryption"],
        "options": [
            {"key": "A", "text": "Reduces handshake latency to 1-RTT (or 0-RTT resumption) and removes insecure legacy ciphers", "is_correct": True},
            {"key": "B", "text": "Replaces public key cryptography with symmetric pre-shared keys only", "is_correct": False},
            {"key": "C", "text": "Eliminates certificate authorities in favor of blockchain proofs", "is_correct": False},
            {"key": "D", "text": "Allows plaintext HTTP traffic over encrypted UDP tunnels", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Modern Protocols",
        "subtopic": "HTTP/3 & QUIC",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "Why does HTTP/3 utilize the QUIC protocol over UDP instead of TCP?",
        "explanation": "QUIC multiplexes independent streams over UDP, eliminating TCP's Head-of-Line (HoL) blocking where packet loss on one stream stalls all other streams.",
        "marks": 1,
        "tags": ["networking", "http3", "quic", "head-of-line"],
        "options": [
            {"key": "A", "text": "To eliminate TCP Head-of-Line blocking across multiplexed streams during packet loss", "is_correct": True},
            {"key": "B", "text": "Because UDP packets are immune to internet routing loops", "is_correct": False},
            {"key": "C", "text": "To bypass operating system kernel networking stacks using raw sockets", "is_correct": False},
            {"key": "D", "text": "Because TCP does not support TLS encryption", "is_correct": False}
        ]
    },
    {
        "technology": "Computer Networks",
        "topic": "Routing",
        "subtopic": "BGP (Border Gateway Protocol)",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What type of routing protocol is BGP (Border Gateway Protocol) classified as?",
        "explanation": "BGP is a Path-Vector routing protocol used to exchange routing and reachability information among Autonomous Systems (AS) across the global Internet.",
        "marks": 1,
        "tags": ["networking", "bgp", "routing", "autonomous-systems"],
        "options": [
            {"key": "A", "text": "Path-Vector exterior gateway protocol", "is_correct": True},
            {"key": "B", "text": "Link-State interior gateway protocol", "is_correct": False},
            {"key": "C", "text": "Distance-Vector broadcast algorithm", "is_correct": False},
            {"key": "D", "text": "Centralized software-defined flow controller", "is_correct": False}
        ]
    },

    # =========================================================================
    # 13. AI & MACHINE LEARNING (12 Questions)
    # =========================================================================
    {
        "technology": "AI/ML",
        "topic": "Machine Learning Basics",
        "subtopic": "Learning Paradigms",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What distinguishes Supervised Learning from Unsupervised Learning?",
        "explanation": "Supervised learning trains models on labeled input-output pairs, whereas unsupervised learning identifies patterns and clusters in unlabeled data without target labels.",
        "marks": 1,
        "tags": ["ai/ml", "supervised", "unsupervised"],
        "options": [
            {"key": "A", "text": "Supervised learning uses labeled training data; unsupervised learning uses unlabeled data", "is_correct": True},
            {"key": "B", "text": "Supervised learning requires human code review for every prediction", "is_correct": False},
            {"key": "C", "text": "Unsupervised learning is exclusively for linear regression models", "is_correct": False},
            {"key": "D", "text": "Supervised models run on CPUs, while unsupervised models require GPUs", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Machine Learning Basics",
        "subtopic": "Overfitting vs Underfitting",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "What is 'Overfitting' in a machine learning model?",
        "explanation": "Overfitting occurs when a model learns the training data noise and details too well, performing excellently on training data but generalizing poorly to unseen validation data.",
        "marks": 1,
        "tags": ["ai/ml", "overfitting", "generalization"],
        "options": [
            {"key": "A", "text": "The model fits training data too closely, failing to generalize to unseen test data", "is_correct": True},
            {"key": "B", "text": "The model is too simple to capture underlying patterns in training data", "is_correct": False},
            {"key": "C", "text": "The training process terminates prematurely due to memory exhaustion", "is_correct": False},
            {"key": "D", "text": "The model produces outputs strictly between 0 and 1", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Evaluation Metrics",
        "subtopic": "Confusion Matrix",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "In a binary classification confusion matrix, what is a 'False Positive'?",
        "explanation": "A False Positive (Type I error) occurs when the model incorrectly predicts the positive class for an actual negative sample.",
        "marks": 1,
        "tags": ["ai/ml", "metrics", "confusion-matrix"],
        "options": [
            {"key": "A", "text": "An actual negative instance incorrectly predicted as positive", "is_correct": True},
            {"key": "B", "text": "An actual positive instance correctly predicted as positive", "is_correct": False},
            {"key": "C", "text": "An actual positive instance incorrectly predicted as negative", "is_correct": False},
            {"key": "D", "text": "A corrupt training sample excluded by the data loader", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Linear Models",
        "subtopic": "Regression vs Classification",
        "difficulty": QuestionDifficultyEnum.BEGINNER,
        "question_text": "Despite its name, what task is 'Logistic Regression' predominantly used for?",
        "explanation": "Logistic Regression uses the sigmoid function to map linear combinations of features to probability values between 0 and 1, used for classification tasks.",
        "marks": 1,
        "tags": ["ai/ml", "logistic-regression", "classification"],
        "options": [
            {"key": "A", "text": "Classification (e.g. binary outcome prediction)", "is_correct": True},
            {"key": "B", "text": "Continuous real-valued price prediction", "is_correct": False},
            {"key": "C", "text": "Clustering high-dimensional unstructured point clouds", "is_correct": False},
            {"key": "D", "text": "Reinforcement learning agent pathfinding", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Evaluation Metrics",
        "subtopic": "Precision vs Recall",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "In a machine learning model predicting a severe medical disease, why would you prioritize high Recall over high Precision?",
        "explanation": "Recall measures the proportion of actual positives identified (TP / (TP + FN)). In medical screening, missing a positive case (False Negative) can be fatal, making high recall paramount.",
        "marks": 1,
        "tags": ["ai/ml", "metrics", "recall", "precision"],
        "options": [
            {"key": "A", "text": "To minimize false negatives, ensuring nearly all diseased patients are flagged", "is_correct": True},
            {"key": "B", "text": "To guarantee that every flagged patient is 100% guaranteed to be sick", "is_correct": False},
            {"key": "C", "text": "To speed up gradient descent convergence during model training", "is_correct": False},
            {"key": "D", "text": "To prevent overfitting on the validation dataset", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Optimization",
        "subtopic": "Gradient Descent",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "What is the role of the 'Learning Rate' hyperparameter in Gradient Descent optimization?",
        "explanation": "The learning rate controls the step size taken in the direction of the negative gradient at each optimization iteration. If too high, it may diverge; if too low, it converges slowly.",
        "marks": 1,
        "tags": ["ai/ml", "gradient-descent", "optimization", "learning-rate"],
        "options": [
            {"key": "A", "text": "It determines the step size taken in the direction of the negative loss gradient", "is_correct": True},
            {"key": "B", "text": "It specifies the number of hidden layers in a neural network", "is_correct": False},
            {"key": "C", "text": "It sets the percentage of training samples held out for cross-validation", "is_correct": False},
            {"key": "D", "text": "It measures model accuracy on unseen test data", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Model Theory",
        "subtopic": "Bias-Variance Tradeoff",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "In the Bias-Variance tradeoff, what symptom characterizes a model with high variance?",
        "explanation": "High variance means the model is overly sensitive to fluctuations and noise in the training set, resulting in low training error but high test/validation error (overfitting).",
        "marks": 1,
        "tags": ["ai/ml", "bias-variance", "overfitting"],
        "options": [
            {"key": "A", "text": "Low training error but high generalization error on unseen test data", "is_correct": True},
            {"key": "B", "text": "High training error and high test error simultaneously (underfitting)", "is_correct": False},
            {"key": "C", "text": "Zero loss across all conceivable input distributions", "is_correct": False},
            {"key": "D", "text": "Inability to converge during backpropagation", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Neural Networks",
        "subtopic": "Activation Functions",
        "difficulty": QuestionDifficultyEnum.INTERMEDIATE,
        "question_text": "Why is the ReLU (Rectified Linear Unit) activation function favored over Sigmoid in deep hidden layers?",
        "explanation": "ReLU (f(x) = max(0, x)) has a constant derivative of 1 for positive inputs, which largely avoids the vanishing gradient problem encountered in deep networks with Sigmoid or Tanh.",
        "marks": 1,
        "tags": ["ai/ml", "neural-networks", "relu", "activation"],
        "options": [
            {"key": "A", "text": "It mitigates the vanishing gradient problem and is computationally efficient to compute", "is_correct": True},
            {"key": "B", "text": "It bounds activations strictly between -1 and +1", "is_correct": False},
            {"key": "C", "text": "It completely eliminates the possibility of dead neurons", "is_correct": False},
            {"key": "D", "text": "It provides probabilistic outputs summing to 1.0", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Deep Learning",
        "subtopic": "Transformers & Attention",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the computational complexity of the standard Scaled Dot-Product Attention mechanism with respect to sequence length N?",
        "explanation": "Standard Self-Attention computes an N x N attention matrix (Q * K^T), resulting in O(N^2) quadratic time and memory complexity with respect to sequence length N.",
        "marks": 1,
        "tags": ["ai/ml", "transformers", "attention", "complexity"],
        "options": [
            {"key": "A", "text": "O(N^2) quadratic complexity", "is_correct": True},
            {"key": "B", "text": "O(N log N)", "is_correct": False},
            {"key": "C", "text": "O(N) strictly linear", "is_correct": False},
            {"key": "D", "text": "O(1)", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Deep Learning",
        "subtopic": "Regularization Techniques",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "How does Dropout regularize deep neural networks during training?",
        "explanation": "Dropout randomly sets a fraction p of hidden units' activations to zero during each forward training pass, preventing co-adaptation of feature detectors and simulating an ensemble of sub-networks.",
        "marks": 1,
        "tags": ["ai/ml", "dropout", "regularization", "deep-learning"],
        "options": [
            {"key": "A", "text": "Randomly deactivates a fraction of neurons per forward pass, preventing feature co-adaptation", "is_correct": True},
            {"key": "B", "text": "Drops training samples with high loss values from the epoch", "is_correct": False},
            {"key": "C", "text": "Penalizes model weights using L1 Laplace priors", "is_correct": False},
            {"key": "D", "text": "Clips gradient values above a pre-set threshold", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Neural Networks",
        "subtopic": "Batch Normalization",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "What is the primary operational effect of Batch Normalization in deep network training?",
        "explanation": "Batch Normalization stabilizes and standardizes layer input distributions across mini-batches, smoothing the optimization landscape and allowing higher learning rates while reducing sensitivity to parameter initialization.",
        "marks": 1,
        "tags": ["ai/ml", "batch-normalization", "deep-learning"],
        "options": [
            {"key": "A", "text": "Standardizes layer inputs to zero mean and unit variance per batch, smoothing the optimization landscape", "is_correct": True},
            {"key": "B", "text": "Converts floating-point 32 weights into 8-bit integers", "is_correct": False},
            {"key": "C", "text": "Forces the learning rate to decay exponentially on every batch", "is_correct": False},
            {"key": "D", "text": "Replaces gradient descent with evolutionary genetic algorithms", "is_correct": False}
        ]
    },
    {
        "technology": "AI/ML",
        "topic": "Modern Generative AI",
        "subtopic": "RLHF & Alignment",
        "difficulty": QuestionDifficultyEnum.ADVANCED,
        "question_text": "In Large Language Model alignment, what does RLHF stand for?",
        "explanation": "RLHF stands for 'Reinforcement Learning from Human Feedback', where a reward model trained on human preference rankings guides policy optimization (e.g. using PPO) to align model outputs with human intent.",
        "marks": 1,
        "tags": ["ai/ml", "rlhf", "llm", "alignment"],
        "options": [
            {"key": "A", "text": "Reinforcement Learning from Human Feedback", "is_correct": True},
            {"key": "B", "text": "Recursive Linear Heuristic Filtering", "is_correct": False},
            {"key": "C", "text": "Real-time Latent Hyperparameter Fine-tuning", "is_correct": False},
            {"key": "D", "text": "Residual Loss Heuristic Forensics", "is_correct": False}
        ]
    }
,
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
