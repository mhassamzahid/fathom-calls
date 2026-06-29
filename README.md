# Won clients export

Run:

```bash
python3 export_won_lead_calls.py
```

The script uses the GoHighLevel credentials already in `.env`, selects the 30
most recently marked-won opportunities in `PIPELINE_ID` owned by Haitham,
Daniel, or Christian, and writes a timestamped client CSV to `exports/`.

Each row contains the opportunity, linked client/contact details, and the GHL
owner's ID and display name. No Fathom API calls are made.
