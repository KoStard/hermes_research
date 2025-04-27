## Generic
- This codebase follows Daoism. The code should flow like water, non-doing, not forced, natural code.
- The code should remain flexible. Don't repeat, don't create many tests for the same capability, keep things lean, to easily adjust and change
- Development is partitioned by subpackage. Don't spread development throughout multiple subpackages. Start development on one module, finish, run the tests, then move to the next. Don't parallelize.
- Always write production code. Code that you can happily publish online or let a teammate to review.
- Never try to solve vague problem directly. Instead, ask for clarifications or more information, write a high level plan and review, then break down into subproblems, create a tracker document with a checklist, and step by step solve while maintaining the tracker document.
- Use """ for multiline strings

## Testing
- Create unit tests for each package, verifying the public methods
- Use clear naming pattern for the test names: `test_methodName_expectedBehaviour_inWhichSituation` - even if the method_name uses snake case, convert it to camelCase like methodName
- Test-driven development - write the unit test for the capability you want, then implement
- For testing using pytest, use fixtures if needed
- In the tests write dummy data, never put real paths/names/data
- When checking strings, verify the whole string at once, don't just check pieces. Use multiline text blocks if needed. So write only one assert if you anyway want to verify the whole string.
- Use AAA (Arrange, Act, Assert)
- Create a class per test file, add the unit tests inside the class

## Implementation

- Create subpackages in python
- Create interface (ABC) in __init__.py, don't import the implementation here
- Use dependency injection from the `main` function when instantiating the implementations
- Have separate files for the implementation classes
- Nest packages logically
- Check if the interface needs to be updated, does it pass all the necessary information?
- Have detailed logging (through `logger = logging.getLogger(__name__)`) with debug, concise with info
- In case you are lacking information about another class in a different subpackage, that means the interface is not good enough defined. Update the interface, maybe add return type, documentation, then ask the user to work with the team to make sure the implementation matches that interface. You can't have access to the implementation from a different subpackage.