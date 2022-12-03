**Specifications**

- **Concept**: Application who can store information about user and their favourite location (restaurant, view, park)

- **Features**: recommendations for users based on their saved history

  1. Dummy users: some pre-definite places 

  2. Establish a unique profile for each user (private profile)

     - Extract comment from these places to determine the kind of places they like 
       - Tools: Bert-topic, Mood Classifier [LUCAS]

     - Extract images for similar atmosphere
       - Tools: U-net with data-sets [ARTHUR]

  3. Establish a list of places where we can look for common features

     - google maps with given km distance 

     - restaurants trip advisor with similar comments
     - search from google images top 10 and find location from these places (to discuss)