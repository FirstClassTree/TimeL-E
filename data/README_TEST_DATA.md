## Explanation for Demo Data Selection

In the Instacart dataset (and similar e-commerce ML datasets),
Every user is either a train or test user.
Their order history is labeled as follows:

*    train users: Their last order is a train order (used for model validation).  
*    test users: Their last order is a test order (used for model evaluation).

In both cases, every order except the last one (for that user) is in prior.


For demo purposes (and for proper evaluation in the ML context), we want the model to:

*    See user’s full history up to and including their "train" order (but not their "test" order!)  
*    Predict what is in the "test" order, which is the "holdout" for evaluation.

We will demo the ML pipeline using this exact split, just like a real competition.  
With this strategy, we will achieve unbiased demo dataset for the ML showcase.

Note; test order metadata is included so that the model can make a prediction for the test order.  
e.g "What does this user tend to order on Mondays at 10am?"

