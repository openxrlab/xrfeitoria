import http.client

conn = http.client.HTTPSConnection("circleci.com")

headers = {"Circle-Token", "$CIRCLE_TOKEN"}

conn.request("GET", "/api/v2/workflow/$CIRCLE_WORKFLOW_ID/job", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
