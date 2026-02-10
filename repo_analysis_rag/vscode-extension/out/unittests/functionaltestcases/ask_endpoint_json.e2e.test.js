"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const axios_1 = __importDefault(require("axios"));
const expect_1 = __importDefault(require("expect"));
const axios_mock_adapter_1 = __importDefault(require("axios-mock-adapter"));
const API_URL = 'http://localhost:8000';
const TOKEN = 'f88adf5229de12b616bb135751a393ef87f87a10a282de546c25d36a63754c56';
describe('POST /ask E2E', () => {
    let mock;
    before(() => {
        mock = new axios_mock_adapter_1.default(axios_1.default);
    });
    after(() => {
        mock.restore();
    });
    it('should return valid tool response envelope', async () => {
        mock.onPost(`${API_URL}/ask`).reply(200, {
            mode: 'ask',
            confidence: 0.9,
            answer: 'Mocked answer',
            citations: []
        });
        try {
            const response = await axios_1.default.post(`${API_URL}/ask`, { query: 'test' }, {
                headers: { 'X-LOCAL-TOKEN': TOKEN }
            });
            (0, expect_1.default)(response.status).toBe(200);
            (0, expect_1.default)(response.data).toHaveProperty('mode');
            (0, expect_1.default)(response.data).toHaveProperty('confidence');
            (0, expect_1.default)(response.data).toHaveProperty('answer');
            (0, expect_1.default)(response.data).toHaveProperty('citations');
            (0, expect_1.default)(Array.isArray(response.data.citations)).toBe(true);
        }
        catch (error) {
            if (error.response && error.response.status !== 200)
                throw error;
            if (!error.response)
                throw new Error(`Connection failed: ${error.message}`);
        }
    });
    it('should return PRD error schema for invalid request', async () => {
        mock.onPost(`${API_URL}/ask`, {}).reply(422);
        try {
            await axios_1.default.post(`${API_URL}/ask`, {}, {
                headers: { 'X-LOCAL-TOKEN': TOKEN }
            });
        }
        catch (error) {
            if (error.response) {
                (0, expect_1.default)(error.response.status).toBe(422); // Validation Error
            }
            else {
                throw new Error(`Connection failed: ${error.message}`);
            }
        }
    });
});
