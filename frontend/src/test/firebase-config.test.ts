import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Firebase Configuration', () => {
  describe('firebase.json structure', () => {
    it('should have valid JSON structure', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      
      // Should parse without throwing
      expect(() => JSON.parse(configContent)).not.toThrow();
    });

    it('should have hosting configuration', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config).toHaveProperty('hosting');
      expect(config.hosting).toBeDefined();
    });

    it('should configure dist as public directory', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config.hosting.public).toBe('dist');
    });

    it('should have ignore patterns', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config.hosting.ignore).toBeDefined();
      expect(Array.isArray(config.hosting.ignore)).toBe(true);
      expect(config.hosting.ignore.length).toBeGreaterThan(0);
    });
  });

  describe('SPA routing configuration', () => {
    it('should include rewrite rules', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config.hosting.rewrites).toBeDefined();
      expect(Array.isArray(config.hosting.rewrites)).toBe(true);
    });

    it('should have catch-all rewrite to index.html', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      const catchAllRewrite = config.hosting.rewrites.find(
        (rule: { source: string; destination: string }) => 
          rule.source === '**' && rule.destination === '/index.html'
      );
      
      expect(catchAllRewrite).toBeDefined();
    });
  });

  describe('Cache headers configuration', () => {
    it('should have headers configuration', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config.hosting.headers).toBeDefined();
      expect(Array.isArray(config.hosting.headers)).toBe(true);
    });

    it('should configure long-term caching for static assets', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      const staticAssetRule = config.hosting.headers.find(
        (rule: { source: string }) => 
          rule.source.includes('js') || rule.source.includes('css')
      );
      
      expect(staticAssetRule).toBeDefined();
      
      const cacheHeader = staticAssetRule.headers.find(
        (header: { key: string; value: string }) => 
          header.key === 'Cache-Control'
      );
      
      expect(cacheHeader).toBeDefined();
      expect(cacheHeader.value).toContain('max-age=31536000');
      expect(cacheHeader.value).toContain('immutable');
    });

    it('should configure short-term caching for HTML', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      const htmlRule = config.hosting.headers.find(
        (rule: { source: string }) => rule.source === 'index.html'
      );
      
      expect(htmlRule).toBeDefined();
      
      const cacheHeader = htmlRule.headers.find(
        (header: { key: string; value: string }) => 
          header.key === 'Cache-Control'
      );
      
      expect(cacheHeader).toBeDefined();
      expect(cacheHeader.value).toContain('max-age=3600');
      expect(cacheHeader.value).toContain('must-revalidate');
    });

    it('should have cache headers for all common static asset types', () => {
      const configPath = join(__dirname, '../../firebase.json');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      const staticAssetRule = config.hosting.headers.find(
        (rule: { source: string }) => 
          rule.source.includes('js') || rule.source.includes('css')
      );
      
      // Check that the source pattern includes common asset types
      const assetTypes = ['js', 'css', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'woff', 'woff2', 'ttf', 'eot'];
      const sourcePattern = staticAssetRule.source;
      
      assetTypes.forEach(type => {
        expect(sourcePattern).toContain(type);
      });
    });
  });

  describe('.firebaserc configuration', () => {
    it('should have valid JSON structure', () => {
      const configPath = join(__dirname, '../../.firebaserc');
      const configContent = readFileSync(configPath, 'utf-8');
      
      // Should parse without throwing
      expect(() => JSON.parse(configContent)).not.toThrow();
    });

    it('should have projects configuration', () => {
      const configPath = join(__dirname, '../../.firebaserc');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config).toHaveProperty('projects');
      expect(config.projects).toBeDefined();
    });

    it('should have default project configured', () => {
      const configPath = join(__dirname, '../../.firebaserc');
      const configContent = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(configContent);
      
      expect(config.projects).toHaveProperty('default');
      expect(typeof config.projects.default).toBe('string');
      expect(config.projects.default.length).toBeGreaterThan(0);
    });
  });
});
