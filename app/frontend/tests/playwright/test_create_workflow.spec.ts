import { test, expect } from '@playwright/test';

test('create workflow from standard tasks', async ({ page }) => {
    // Go to the app
    await page.goto('http://localhost:5173');

    // Wait for the controls section to be visible
    await expect(page.getByRole('heading', { name: 'Controls' })).toBeVisible();

    // Click the "Start New Workflow" button
    await page.getByRole('button', { name: 'Start New Workflow' }).click();

    // Wait for the workflow list to update
    await expect(page.getByRole('heading', { name: /Laboratory Automation Framework/i })).toBeVisible();

    // Check that the new workflow appears in the workflow list
    const workflowList = page.locator('.WorkflowList');
    await expect(workflowList).toContainText('My Workflow');

    // Optionally, check that tasks for centrifuge and incubator are present
    await expect(workflowList).toContainText('Sample Prep');
    await expect(workflowList).toContainText('Analysis');

    // Optionally, check lab status visuals update
    await expect(page.getByRole('heading', { name: 'Lab Status' })).toBeVisible();
    await expect(page.locator('.LabVisual')).toBeVisible();
});
