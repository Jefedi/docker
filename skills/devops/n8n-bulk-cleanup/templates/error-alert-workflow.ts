// n8n Error Alert Workflow Template
// Error Trigger → Code (format) → HTTP Request (ntfy)
// Notifies ntfy when ANY workflow crashes in production mode.
//
// Usage:
// 1. Validate with mcp__n8n_mcp__validate_workflow
// 2. Create with mcp__n8n_mcp__create_workflow_from_code
// 3. Set auth type on HTTP node: updateNodeParameters {authentication: "predefinedCredentialType", nodeCredentialType: "httpBearerAuth"}
// 4. Link credential: setNodeCredential {credentialId: "<ntfy-cred-id>", credentialKey: "httpBearerAuth", credentialName: "NTFY"}
// 5. Publish: mcp__n8n_mcp__publish_workflow
// 6. Link to other workflows: setWorkflowSettings {errorWorkflow: "<this-workflow-id>"}

import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

const errorTrigger = trigger({
  type: 'n8n-nodes-base.errorTrigger',
  version: 1,
  config: { name: 'Error Trigger', position: [0, 0] },
  output: [{ execution: { id: 1, error: { message: 'test', node: { name: 'TestNode' } } }, workflow: { name: 'TestWF' } }]
});

const formatAlert = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Format Alert',
    position: [224, 0],
    parameters: {
      jsCode: [
        'const error = $json;',
        'const wfName = error.workflow?.name || error.workflowId || "Unknown";',
        'const execId = error.execution?.id || error.executionId || "?";',
        'const errorMsg = error.execution?.error?.message || error.message || "Unknown error";',
        'const nodeName = error.execution?.error?.node?.name || "?";',
        '',
        'const message = "Workflow: " + wfName + "\\nNode: " + nodeName + "\\nErreur: " + errorMsg + "\\nExecution: #" + execId;',
        '',
        'return [{ json: { workflowName: wfName, message: message } }];'
      ].join('\n')
    }
  },
  output: [{ workflowName: 'TestWF', message: 'Workflow: TestWF\nNode: TestNode\nErreur: test\nExecution: #1' }]
});

const sendNtfy = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Send ntfy',
    position: [448, 0],
    executeOnce: true,
    parameters: {
      method: 'POST',
      url: 'https://ntfy.jefe.ovh/n8n-errors',
      sendHeaders: true,
      headerParameters: {
        parameters: [
          { name: 'Title', value: expr('🔴 {{ $json.workflowName }} a crashé') },
          { name: 'Priority', value: 'urgent' },
          { name: 'Tags', value: 'warning' }
        ]
      },
      sendBody: true,
      contentType: 'raw',
      rawContentType: 'text/plain',
      body: expr('{{ $json.message }}')
    },
    credentials: {
      httpBearerAuth: newCredential('NTFY')
    }
  },
  output: [{ success: true }]
});

export default workflow('error-alert-ntfy', '🔔 Error Alert → ntfy')
  .add(errorTrigger)
  .to(formatAlert)
  .to(sendNtfy);