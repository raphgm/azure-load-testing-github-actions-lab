// Provisions an Azure Load Testing resource and grants the CI/CD service
// principal the "Load Test Contributor" role, scoped to this resource group.

@description('Name of the Azure Load Testing resource')
param loadTestName string = 'payments-api-loadtest'

@description('Azure region for the Load Testing resource')
param location string = resourceGroup().location

@description('Object ID of the service principal (or Entra app) that GitHub Actions authenticates as')
param principalId string

@description('Role definition ID for "Load Test Contributor"')
var loadTestContributorRoleId = '749a398d-560b-491b-bb21-08924219302e'

resource loadTest 'Microsoft.LoadTestService/loadTests@2023-12-01-preview' = {
  name: loadTestName
  location: location
  properties: {}
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, loadTestContributorRoleId)
  scope: loadTest
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', loadTestContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output loadTestResourceId string = loadTest.id
output loadTestResourceName string = loadTest.name
