TravelPage sends structured travel input and wallet metadata through travelApi to Spring TravelController.
DemoFareProvider returns labeled all-passenger fare totals for Delhi ↔ Mumbai.
TravelService feeds priced PurchaseContexts into the shared OptimizationService; there is no second eligibility, cost or ranking engine.
The response maps each route to its fare and retains provider warnings and exclusions.
Legacy demoFlights.ts is kept for historical prototype model tests, not active fare search.
