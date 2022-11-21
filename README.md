# Monad noflight

The base idea is that the plane navigates to a point that is ~20 units away from the landing side of the airport. 
Around that point the airplane realises the close proximity of the airport and matches the direction with it. 

### Improvement:

The program isn't perfect and the same offset-values probably don't yet work for all levels
1. Dodging of other planes should have a order in which the planes dodge others so that all planes don't dodge equally ( perhaps by id order )
2. The offset-values should be refined
3. Code refactoring ( methods grouped to modules, some reasoning behind offset constants )
