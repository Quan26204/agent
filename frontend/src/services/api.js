
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 15000,
});

export async function getPlans(params = {}) {
  const response = await api.get("/orchestrator/plans", {
    params,
  });

  return response.data;
}

export async function getPendingPlans(params = {}) {
  const response = await api.get(
    "/orchestrator/plans/pending",
    { params }
  );

  return response.data;
}

export async function getPlan(planId) {
  const response = await api.get(
    `/orchestrator/plans/${planId}`
  );

  return response.data;
}

export async function approvePlan(planId) {
  const response = await api.post(
    `/orchestrator/plans/${planId}/approve`
  );

  return response.data;
}

export async function rejectPlan(planId) {
  const response = await api.post(
    `/orchestrator/plans/${planId}/reject`
  );

  return response.data;
}

export async function executePlan(planId) {
  const response = await api.post(
    `/orchestrator/plans/${planId}/execute`
  );

  return response.data;
}

export default api;
