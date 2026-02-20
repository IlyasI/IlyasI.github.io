import { test, expect } from '@playwright/test';

test.describe('Page load', () => {
  test('renders with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Ilyas Ibragimov/);
  });

  test('hero section displays name and typing animation', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.hero-name')).toHaveText('Ilyas Ibragimov');
    // Wait for typing animation to complete
    await expect(page.locator('#typed-title')).toHaveText('Senior Software Developer', { timeout: 5000 });
  });

  test('canvas element exists', async ({ page }) => {
    await page.goto('/');
    const canvas = page.locator('#canvas');
    await expect(canvas).toBeAttached();
  });
});

test.describe('Navigation', () => {
  test('nav links exist and point to correct sections', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.nav-logo')).toHaveText('~/ilyasi');
    await expect(page.locator('.nav-links a[href="#about"]')).toBeVisible();
    await expect(page.locator('.nav-links a[href="#experience"]')).toBeVisible();
    await expect(page.locator('.nav-links a[href="#projects"]')).toBeVisible();
    await expect(page.locator('.nav-links a[href="#skills"]')).toBeVisible();
    await expect(page.locator('.nav-links a[href="#education"]')).toBeVisible();
  });

  test('nav gets scrolled class on scroll', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('.nav');
    await expect(nav).not.toHaveClass(/nav-scrolled/);
    await page.evaluate(() => window.scrollTo(0, 200));
    await expect(nav).toHaveClass(/nav-scrolled/);
  });

  test('resume download link exists', async ({ page }) => {
    await page.goto('/');
    const resumeLink = page.locator('.nav-links a[href="resume.pdf"]');
    await expect(resumeLink).toBeVisible();
    await expect(resumeLink).toHaveAttribute('download', 'IlyasIbragimov-Resume.pdf');
  });
});

test.describe('Content sections', () => {
  test('experience section has all companies', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.exp-company').nth(0)).toHaveText('Two Sigma');
    await expect(page.locator('.exp-company').nth(1)).toHaveText('Blueshift Asset Management');
    await expect(page.locator('.exp-company').nth(2)).toHaveText('Fidessa');
  });

  test('projects section has project cards', async ({ page }) => {
    await page.goto('/');
    const cards = page.locator('.project-card');
    await expect(cards).toHaveCount(3);
  });

  test('skills section has all categories', async ({ page }) => {
    await page.goto('/');
    const cats = page.locator('.skill-cat');
    await expect(cats).toHaveCount(6);
  });

  test('education section has all entries', async ({ page }) => {
    await page.goto('/');
    const entries = page.locator('.edu-entry');
    await expect(entries).toHaveCount(3);
  });

  test('hero highlights has 5 badges', async ({ page }) => {
    await page.goto('/');
    const highlights = page.locator('.highlight');
    await expect(highlights).toHaveCount(5);
  });
});

test.describe('External links', () => {
  test('all external links have target="_blank" and rel="noopener"', async ({ page }) => {
    await page.goto('/');
    const externalLinks = page.locator('a[href^="https://"]');
    const count = await externalLinks.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const link = externalLinks.nth(i);
      await expect(link).toHaveAttribute('target', '_blank');
      await expect(link).toHaveAttribute('rel', /noopener/);
    }
  });
});

test.describe('Terminal', () => {
  test('trigger button is visible, terminal is hidden by default', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#terminal-trigger')).toBeVisible();
    await expect(page.locator('#terminal')).not.toHaveClass(/open/);
  });

  test('clicking trigger opens terminal', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await expect(page.locator('#terminal')).toHaveClass(/open/);
    await expect(page.locator('#terminal-trigger')).toHaveClass(/hidden/);
  });

  test('close button closes terminal', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await expect(page.locator('#terminal')).toHaveClass(/open/);
    await page.click('#terminal-close');
    await expect(page.locator('#terminal')).not.toHaveClass(/open/);
    await expect(page.locator('#terminal-trigger')).not.toHaveClass(/hidden/);
  });

  test('Escape key closes terminal', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await expect(page.locator('#terminal')).toHaveClass(/open/);
    await page.keyboard.press('Escape');
    await expect(page.locator('#terminal')).not.toHaveClass(/open/);
  });

  test('help command lists available commands', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'help');
    await page.press('#terminal-input', 'Enter');
    const output = page.locator('#terminal-output');
    await expect(output).toContainText('whoami');
    await expect(output).toContainText('experience');
    await expect(output).toContainText('theme light|dark');
    await expect(output).toContainText('gravity');
    await expect(output).toContainText('matrix');
  });

  test('whoami command shows correct info', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'whoami');
    await page.press('#terminal-input', 'Enter');
    const output = page.locator('#terminal-output');
    await expect(output).toContainText('Ilyas Ibragimov');
    await expect(output).toContainText('Two Sigma');
  });

  test('clear command empties terminal output', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'help');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).not.toBeEmpty();
    await page.fill('#terminal-input', 'clear');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toBeEmpty();
  });

  test('unknown command shows error', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'foobar');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('command not found: foobar');
  });

  test('command history works with arrow keys', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'whoami');
    await page.press('#terminal-input', 'Enter');
    await page.fill('#terminal-input', 'skills');
    await page.press('#terminal-input', 'Enter');
    await page.press('#terminal-input', 'ArrowUp');
    await expect(page.locator('#terminal-input')).toHaveValue('skills');
    await page.press('#terminal-input', 'ArrowUp');
    await expect(page.locator('#terminal-input')).toHaveValue('whoami');
    await page.press('#terminal-input', 'ArrowDown');
    await expect(page.locator('#terminal-input')).toHaveValue('skills');
  });
});

test.describe('Theme switching', () => {
  test('theme light command sets light theme', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'theme light');
    await page.press('#terminal-input', 'Enter');
    const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(theme).toBe('light');
  });

  test('theme dark command removes light theme', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'theme light');
    await page.press('#terminal-input', 'Enter');
    await page.fill('#terminal-input', 'theme dark');
    await page.press('#terminal-input', 'Enter');
    const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(theme).toBeNull();
  });

  test('light theme changes background color', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'theme light');
    await page.press('#terminal-input', 'Enter');
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    // Light theme bg should be light (rgb values > 200)
    const match = bg.match(/rgb\((\d+), (\d+), (\d+)\)/);
    expect(parseInt(match[1])).toBeGreaterThan(200);
  });
});

test.describe('Visual commands', () => {
  test('accent command changes accent color', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'accent red');
    await page.press('#terminal-input', 'Enter');
    const accent = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
    );
    expect(accent).toBe('#f87171');
  });

  test('gravity command toggles gravity', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'gravity');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('Gravity on');
    await page.fill('#terminal-input', 'gravity');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('Gravity off');
  });

  test('matrix command toggles matrix mode', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'matrix');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('Matrix mode on');
    const accent = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
    );
    expect(accent).toBe('#00cc44');
  });

  test('speed command changes simulation speed', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'speed 2');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('2x');
  });

  test('reset command restores defaults', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'accent red');
    await page.press('#terminal-input', 'Enter');
    await page.fill('#terminal-input', 'theme light');
    await page.press('#terminal-input', 'Enter');
    await page.fill('#terminal-input', 'reset');
    await page.press('#terminal-input', 'Enter');
    const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(theme).toBeNull();
    await expect(page.locator('#terminal-output')).toContainText('reset to defaults');
  });

  test('particles command changes count', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'particles 100');
    await page.press('#terminal-input', 'Enter');
    await expect(page.locator('#terminal-output')).toContainText('Particle count set to 100');
  });

  test('particles off/on toggles canvas', async ({ page }) => {
    await page.goto('/');
    await page.click('#terminal-trigger');
    await page.fill('#terminal-input', 'particles off');
    await page.press('#terminal-input', 'Enter');
    const display = await page.evaluate(() => document.getElementById('canvas').style.display);
    expect(display).toBe('none');
    await page.fill('#terminal-input', 'particles on');
    await page.press('#terminal-input', 'Enter');
    const display2 = await page.evaluate(() => document.getElementById('canvas').style.display);
    expect(display2).toBe('');
  });
});

test.describe('Scroll reveal', () => {
  test('education section reveals on scroll', async ({ page }) => {
    await page.goto('/');
    // Education is far enough down to not be in initial viewport
    const panel = page.locator('#education .glass-panel');
    // Scroll to it
    await page.locator('#education').scrollIntoViewIfNeeded();
    await expect(panel).toHaveClass(/revealed/, { timeout: 2000 });
  });
});

test.describe('Responsive', () => {
  test('nav links hidden on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.locator('.nav-links')).not.toBeVisible();
  });

  test('projects grid stacks on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const grid = page.locator('.projects-grid');
    const cols = await grid.evaluate(el => getComputedStyle(el).gridTemplateColumns);
    // Should be single column on mobile
    const colCount = cols.split(' ').length;
    expect(colCount).toBe(1);
  });
});

test.describe('Theme toggle', () => {
  test('theme toggle button exists in nav', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#theme-toggle')).toBeVisible();
  });

  test('clicking theme toggle switches to light mode', async ({ page }) => {
    await page.goto('/');
    await page.click('#theme-toggle');
    const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(theme).toBe('light');
  });

  test('clicking theme toggle twice returns to dark mode', async ({ page }) => {
    await page.goto('/');
    await page.click('#theme-toggle');
    await page.click('#theme-toggle');
    const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(theme).toBeNull();
  });
});

test.describe('Footer', () => {
  test('footer has copyright notice', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.footer-copyright')).toContainText('2026 Ilyas Ibragimov');
  });
});

test.describe('Project card layout', () => {
  test('last odd project card spans full width on desktop', async ({ page }) => {
    await page.goto('/');
    const lastCard = page.locator('.project-card').last();
    const gridColumn = await lastCard.evaluate(el => getComputedStyle(el).gridColumn);
    expect(gridColumn).toBe('1 / -1');
  });
});
