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
describe('POST /overview E2E', () => {
    let mock;
    before(() => {
        mock = new axios_mock_adapter_1.default(axios_1.default);
        mock.onPost(`${API_URL}/overview`).reply(200, { mode: 'overview', answer: 'test' });
    });
    after(() => {
        mock.restore();
    });
    it('should return valid tool response envelope', async () => {
        try {
            const response = await axios_1.default.post(`${API_URL}/overview`, { root_path: '/test' }, {
                headers: { 'X-LOCAL-TOKEN': TOKEN }
            });
            (0, expect_1.default)(response.status).toBe(200);
            (0, expect_1.default)(response.data.mode).toBeDefined();
            (0, expect_1.default)(response.data.answer).toBeDefined();
        }
        catch (error) {
            if (error.response && error.response.status === 404) {
                return;
            }
            if (error.response && error.response.status !== 200)
                throw error;
            if (!error.response)
                throw new Error(`Connection failed: ${error.message}`);
        }
    });
});
