/** Data locations. PM_DATA_DIR moves every writable store (accounts, jobs, reports, cache) at once. */
import { resolve, join } from 'node:path';
const DEFAULT_ROOT = resolve(import.meta.dirname, '../data');
// Read on every call so tests (and operators) can set PM_DATA_DIR before first use.
export const dataRoot = () => (process.env.PM_DATA_DIR ? resolve(process.env.PM_DATA_DIR) : DEFAULT_ROOT);
export const privateRoot = () => join(dataRoot(), 'private');
export const jobsRoot = () => join(privateRoot(), 'institutional-jobs');
export const reportsRoot = () => join(dataRoot(), 'reports');
export const cacheRoot = () => join(dataRoot(), 'cache');
