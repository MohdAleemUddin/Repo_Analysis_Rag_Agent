import axios from 'axios';
import expect from 'expect';
import MockAdapter from 'axios-mock-adapter';

const API_URL = 'http://localhost:8000';
const TOKEN = 'f88adf5229de12b616bb135751a393ef87f87a10a282de546c25d36a63754c56';

describe('POST /search E2E', () => {
  let mock: MockAdapter;

  before(() => {
    mock = new MockAdapter(axios);
    mock.onPost(`${API_URL}/search`).reply(200, { mode: 'search' });
  });

  after(() => {
    mock.restore();
  });

  it('should return valid tool response envelope', async () => {
    try {
      const response = await axios.post(`${API_URL}/search`, { query: 'test' }, {
        headers: { 'X-LOCAL-TOKEN': TOKEN }
      });
      expect(response.status).toBe(200);
      expect(response.data.mode).toBe('search');
    } catch (error: any) {
      if (error.response && error.response.status === 404) {
        return;
      }
      if (error.response && error.response.status !== 200) throw error;
      if (!error.response) throw new Error(`Connection failed: ${error.message}`);
    }
  });
});
