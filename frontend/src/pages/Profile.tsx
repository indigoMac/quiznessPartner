import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Button from "../components/Button";

function formatMemberSince(value?: string) {
  if (!value) return "Unknown";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown";
  return parsed.toLocaleDateString();
}

export default function Profile() {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-6">
        <h1 className="text-2xl font-bold">Profile</h1>
        <dl className="space-y-4">
          <div>
            <dt className="text-sm text-gray-500 dark:text-gray-400">Email</dt>
            <dd className="text-lg font-medium">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500 dark:text-gray-400">
              Member since
            </dt>
            <dd className="text-lg font-medium">
              {formatMemberSince(user?.created_at)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500 dark:text-gray-400">Status</dt>
            <dd className="text-lg font-medium">
              {user?.is_active === false ? "Inactive" : "Active"}
            </dd>
          </div>
        </dl>
        <div className="flex flex-col sm:flex-row gap-3">
          <Link to="/dashboard">
            <Button variant="secondary">Back to dashboard</Button>
          </Link>
          <Button variant="secondary" onClick={logout}>
            Log out
          </Button>
        </div>
      </div>
    </div>
  );
}
