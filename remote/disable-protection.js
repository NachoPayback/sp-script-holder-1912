// Script to disable Vercel deployment protection via API
const https = require('https');

const projectId = 'prj_PYOZTvGyLoeSGZwuxxU0PjiPm8T5'; // From vercel project inspect
const teamId = 'team_8sRODTVgjCgjKyS1RdUzBo5o'; // From .vercel/project.json

// This would require a Vercel API token
// You can get one from: https://vercel.com/account/tokens

const apiToken = process.env.VERCEL_TOKEN;

if (!apiToken) {
  console.log('Please set VERCEL_TOKEN environment variable');
  console.log('Get token from: https://vercel.com/account/tokens');
  process.exit(1);
}

const data = JSON.stringify({
  "protection": {
    "type": "none"
  }
});

const options = {
  hostname: 'api.vercel.com',
  port: 443,
  path: `/v9/projects/${projectId}?teamId=${teamId}`,
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${apiToken}`,
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  
  let responseData = '';
  res.on('data', (chunk) => {
    responseData += chunk;
  });
  
  res.on('end', () => {
    console.log('Response:', responseData);
  });
});

req.on('error', (error) => {
  console.error('Error:', error);
});

req.write(data);
req.end();

console.log('Attempting to disable deployment protection...');