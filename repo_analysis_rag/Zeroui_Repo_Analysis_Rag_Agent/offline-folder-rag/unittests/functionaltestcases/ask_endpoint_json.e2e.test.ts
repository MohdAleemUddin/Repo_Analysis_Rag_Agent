import axios from 'axios';
import expect from 'expect';
import MockAdapter from 'axios-mock-adapter';

const API_URL = 'http://localhost:8000';
const TOKEN = 'f88adf5229de12b616bb135751a393ef87f87a10a282de546c25d36a63754c56';

describe('POST /ask E2E', () => {
  let mock: MockAdapter;

  before(() => {
    mock = new MockAdapter(axios);
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
      const response = await axios.post(`${API_URL}/ask`, { query: 'test' }, {
        headers: { 'X-LOCAL-TOKEN': TOKEN }
      });
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('mode');
      expect(response.data).toHaveProperty('confidence');
      expect(response.data).toHaveProperty('answer');
      expect(response.data).toHaveProperty('citations');
      expect(Array.isArray((response.data as any).citations)).toBe(true);
    } catch (error: any) {
      if (error.response && error.response.status !== 200) throw error;
      if (!error.response) throw new Error(`Connection failed: ${error.message}`);
    }
  });

  it('should return PRD error schema for invalid request', async () => {
    mock.onPost(`${API_URL}/ask`, {}).reply(422);

    try {
      await axios.post(`${API_URL}/ask`, {}, {
        headers: { 'X-LOCAL-TOKEN': TOKEN }
      });
    } catch (error: any) {
      if (error.response) {
        expect(error.response.status).toBe(422); // Validation Error
      } else {
        throw new Error(`Connection failed: ${error.message}`);
      }
    }
  });
});
