import { test, expect } from '@playwright/test';

test.describe('Agentic Mesh Router Simulation E2E', () => {
    const PRODUCTION_URL = 'https://rdcl-agentic-mesh-production.up.railway.app';

    test('should render the dashboard and receive WebSocket data', async ({ page }) => {
        // Navigate to the production URL
        await page.goto(PRODUCTION_URL);

        // Verify the page title and main header
        await expect(page).toHaveTitle(/Agentic Mesh Router/);
        await expect(page.locator('h1')).toContainText('Agentic Mesh Router');

        // Wait for WebSocket data to populate the stats
        // We expect transmissions to go above 0 as the simulation runs
        await expect(page.locator('#stat-tx')).not.toHaveText('0', { timeout: 15000 });

        // Verify the policy engine type is populated
        const policyElement = page.locator('#stat-policy');
        await expect(policyElement).not.toHaveText('Unknown');
        await expect(policyElement).not.toHaveText('Loading...');

        // Wait for nodes to be rendered on the canvas
        const nodes = page.locator('.node');
        await expect(nodes).toHaveCount(15, { timeout: 10000 }); // The simulation initializes 15 nodes

        // Wait for reasoning logs to appear
        const logContainer = page.locator('#log-container > div');
        await expect(logContainer.first()).toBeVisible({ timeout: 10000 });

        // Ensure we are logging FORWARD or DROP actions correctly
        const logText = await page.locator('#log-container').textContent();
        expect(logText).toMatch(/(FORWARD|DROP)/);
    });
});
