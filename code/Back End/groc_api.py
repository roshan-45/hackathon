import os
from groq import Groq
from langchain.agents import Tool, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class GroqLLM:
    def __init__(self, client):
        self.client = client

    def __call__(self, messages, model="llama3-8b-8192"):
        response = self.client.chat.completions.create(
            messages=messages,
            model=model
        )
        return response.choices[0].message.content.strip()
    
    def bind(self, stop=None):
        return self
    
groq_llm = GroqLLM(client)

prompt_template = PromptTemplate(
    input_variables=["log_entry", "agent_scratchpad", "tools", "tool_names"],
    template=(
        '''Your task is to analyze the given log text, which usually contains a date, time, project_id, and details related to transportation management.
        If the log_entry lacks sufficient information, use relevant tools to search the web and provide a solution.
        Focus on identifying any errors or warnings present in the log_entry.
        Log Entry:
        {log_entry}
        Available tools: {tools}
        Tool names: {tool_names}
        Please summarize your findings clearly without any additional notes.
        Current scratchpad: {agent_scratchpad}
        '''
    )
)

def analyze_log(log_entry):
    prompt = prompt_template.format(
        log_entry=log_entry,
        agent_scratchpad="",  
        tools=", ".join([tool.name for tool in tools]), 
        tool_names=", ".join([tool.name for tool in tools])  
    )
    response = groq_llm(messages=[{"role": "user", "content": prompt}])
    return response

# Define a function to perform a web search using SerpAPI
# def web_search(query):
#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": os.environ.get("SERPAPI_API_KEY")  # Use your SerpAPI key from an environment variable
#     }
#     search = GoogleSearch(params)
#     results = search.get_dict()
#     # Extract relevant data from the results
#     if "organic_results" in results:
#         return "\n".join(result['snippet'] for result in results["organic_results"])
#     return "No results found."
# Define tools that the agent can use

tools = [
    Tool(
        name="Log Analyzer",
        func=analyze_log,
        description="Analyzes a log entry for errors or warnings."
    ),
    # Tool(
    #     name="Web Search",
    #     func=web_search,
    #     description="Searches the web for relevant information."
    # )
]

agent = create_react_agent(
    llm=groq_llm, 
    prompt=prompt_template,
    tools=tools
)

log_entry = '''2024-10-11 10:09:06.159	174390	Error	Exception	[006898] Read time out after 10000 millis
    Error while getting response from webservice
cause.PCMilerEngineWS.getResultFaild
	at glog.business.rate.ratedistance.external.PCMilerWSWCFHandler.getResult(PCMilerWSWCFHandler.java:1219)
	at glog.business.rate.ratedistance.external.PCMilerWSWCFHandler.lookupServiceTime(PCMilerWSWCFHandler.java:801)
	at glog.business.rate.ratedistance.external.PCMilerEngineWS.lookupServiceTime(PCMilerEngineWS.java:105)
	at glog.business.rateservicescheduling.ExternalRateServiceEngine.retrieveTransitTime(ExternalRateServiceEngine.java:119)
	at glog.business.rateservicescheduling.ExternalRateServiceEngine.retrieveTransitTime(ExternalRateServiceEngine.java:156)
	at glog.business.rateservicescheduling.NonScheduleRateServiceEngine.getFixedTransitTime(NonScheduleRateServiceEngine.java:323)
	at glog.business.rateservicescheduling.ExternalRateServiceEngine.getFixedTransitTime(ExternalRateServiceEngine.java:313)
	at glog.business.rateservicescheduling.NonScheduleRateServiceEngine.getFixedTransitTime(NonScheduleRateServiceEngine.java:261)
	at glog.business.rateservicescheduling.RateServiceHelper.getMaxTransitTime(RateServiceHelper.java:1147)
	at glog.business.rateservicescheduling.RateServiceHelper.estimateSrcDepotTimeWindow(RateServiceHelper.java:1010)
	at glog.business.rateservicescheduling.RateServiceHelper.estimateOtherStopTimeWindow(RateServiceHelper.java:727)
	at glog.business.rateservicescheduling.RateServiceEngine.drive(RateServiceEngine.java:172)
	at glog.business.rateservicescheduling.RateServiceEngine.drive(RateServiceEngine.java:449)
	at glog.business.rateservicescheduling.RateServiceEngine.calculateRateServiceSolutionWindow(RateServiceEngine.java:1396)
	at glog.business.shipment.LegOptionOptimizer.calculateServiceTime(LegOptionOptimizer.java:1456)
	at glog.business.shipment.LegOptionOptimizer.getCheapestFeasibleOption(LegOptionOptimizer.java:585)
	at glog.business.shipment.LegOptionOptimizer.buildItineraryOptionOnBestLegOptions(LegOptionOptimizer.java:182)
	at glog.business.shipment.ShipmentBuilder.buildBestItineraryOption(ShipmentBuilder.java:1596)
	at glog.business.shipment.ShipmentBuilder.buildShipmentGraph(ShipmentBuilder.java:1635)
	at glog.business.shipment.ShipmentBuilder.buildShipmentGraphCollection(ShipmentBuilder.java:515)
	at glog.business.shipment.ShipmentBuilder.buildShipmentGraphCollection(ShipmentBuilder.java:434)
	at glog.business.consolidation.bulkplan.BuildShipmentGraphCollectionTask.executePlanning(BuildShipmentGraphCollectionTask.java:36)
	at glog.business.util.PlanningTask.execute(PlanningTask.java:14)
	at glog.server.workflow.tasklist.Task.perform(Task.java:51)
	at glog.server.workflow.tasklist.TaskList.executeInCallerThread(TaskList.java:117)
	at glog.business.util.PlanningTaskList.executeInCallerThread(PlanningTaskList.java:79)
	at glog.server.workflow.tasklist.TaskList.execute(TaskList.java:97)
	at glog.server.workflow.tasklist.TaskList.execute(TaskList.java:158)
	at glog.business.consolidation.bulkplan.OrderPlanner.buildDirectShipmentGraphCollection(OrderPlanner.java:1385)
	at glog.business.consolidation.bulkplan.OrderPlanner.makeDirectTShipments(OrderPlanner.java:1296)
	at glog.business.consolidation.bulkplan.OrderPlanner.bulkPlan(OrderPlanner.java:447)
	at glog.business.action.order.OrderActions.planUnassignedOrders(OrderActions.java:1089)
	at glog.business.action.order.BulkPlanActionExecutor.planOrders(BulkPlanActionExecutor.java:481)
	at glog.business.action.order.BulkPlanActionExecutor.planOrders(BulkPlanActionExecutor.java:261)
	at glog.business.session.OrderActionSessionBean.planOrders(OrderActionSessionBean.java:1316)
	at glog.business.session.OrderActionSessionBean.planOrders(OrderActionSessionBean.java:1281)
	at glog.business.session.OrderActionSessionStub.planOrders(OrderActionSessionStub.java:654)
	at glog.server.workflow.adhoc.BulkPlan.executeOrder(BulkPlan.java:75)
	at glog.server.workflow.adhoc.BulkPlan.execute(BulkPlan.java:59)
	at glog.server.workflow.SimpleWorkflow.execute(SimpleWorkflow.java:23)
	at glog.server.workflow.WorkflowSessionBean.execute(WorkflowSessionBean.java:64)
	at glog.server.workflow.WorkflowSessionNonTransStub.execute(WorkflowSessionNonTransStub.java:29)
	at glog.server.workflow.WorkflowManager.execute(WorkflowManager.java:372)
	at glog.server.workflow.Trigger.trigger(Trigger.java:124)
	at glog.util.event.MemoryEventQueueRunnable.processEvent(MemoryEventQueueRunnable.java:146)
	at glog.util.event.MemoryEventQueueRunnable.run(MemoryEventQueueRunnable.java:100)
	at glog.util.event.EventThread.run(EventThread.java:86)
	at java.lang.Thread.run(Thread.java:750)
Caused by: javax.xml.ws.WebServiceException: java.net.SocketTimeoutException: Read time out after 10000 millis
	at com.sun.xml.ws.transport.http.client.HttpClientTransport.readResponseCodeAndMessage(HttpClientTransport.java:210)
	at com.sun.xml.ws.transport.http.client.HttpTransportPipe.createResponsePacket(HttpTransportPipe.java:241)
	at com.sun.xml.ws.transport.http.client.HttpTransportPipe.process(HttpTransportPipe.java:232)
	at weblogic.wsee.jaxws.transport.http.client.WLSHttpTransportPipe.process(WLSHttpTransportPipe.java:30)
	at com.sun.xml.ws.transport.http.client.HttpTransportPipe.processRequest(HttpTransportPipe.java:145)
	at com.sun.xml.ws.transport.DeferredTransportPipe.processRequest(DeferredTransportPipe.java:110)
	at com.sun.xml.ws.api.pipe.Fiber.__doRun(Fiber.java:1136)
	at com.sun.xml.ws.api.pipe.Fiber._doRun(Fiber.java:1050)
	at com.sun.xml.ws.api.pipe.Fiber.doRun(Fiber.java:1019)
	at com.sun.xml.ws.api.pipe.Fiber.runSync(Fiber.java:877)
	at com.sun.xml.ws.client.Stub.process(Stub.java:463)
	at com.sun.xml.ws.client.sei.SEIStub.doProcess(SEIStub.java:191)
	at com.sun.xml.ws.client.sei.SyncMethodHandler.invoke(SyncMethodHandler.java:108)
	at com.sun.xml.ws.client.sei.SyncMethodHandler.invoke(SyncMethodHandler.java:92)
	at com.sun.xml.ws.client.sei.SEIStub.invoke(SEIStub.java:161)
	at com.sun.proxy.$Proxy407.getReports(Unknown Source)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at weblogic.wsee.jaxws.spi.ClientInstanceInvocationHandler.invoke(ClientInstanceInvocationHandler.java:148)
	at com.sun.proxy.$Proxy408.getReports(Unknown Source)
	at glog.business.rate.ratedistance.external.PCMilerWSWCFHandler.getResult(PCMilerWSWCFHandler.java:1205)
	... 47 more
Caused by: java.net.SocketTimeoutException: Read time out after 10000 millis
	at weblogic.socket.NIOInputStream.readInternal(NIOInputStream.java:177)
	at weblogic.socket.NIOInputStream.read(NIOInputStream.java:110)
	at weblogic.socket.NIOInputStream.read(NIOInputStream.java:73)
	at java.io.BufferedInputStream.fill(BufferedInputStream.java:246)
	at java.io.BufferedInputStream.read1(BufferedInputStream.java:286)
	at java.io.BufferedInputStream.read(BufferedInputStream.java:345)
	at weblogic.net.http.MessageHeader.isHTTP(MessageHeader.java:310)
	at weblogic.net.http.MessageHeader.parseHeader(MessageHeader.java:232)
	at weblogic.net.http.HttpClient.parseHTTP(HttpClient.java:564)
	at weblogic.net.http.HttpURLConnection.getInputStream(HttpURLConnection.java:766)
	at weblogic.net.http.SOAPHttpURLConnection.getInputStream(SOAPHttpURLConnection.java:42)
	at weblogic.net.http.HttpURLConnection.getResponseCode(HttpURLConnection.java:1627)
	at com.sun.xml.ws.transport.http.client.HttpClientTransport.readResponseCodeAndMessage(HttpClientTransport.java:206)
	... 69 more
 [batch - 2]'''

response = analyze_log(log_entry)
print("Log Analysis Response:", response)
