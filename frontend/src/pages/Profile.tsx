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
    <div className="mx-auto max-w-xl">
      <div className="card p-5 sm:p-6 space-y-6">
        <div>
          <p className="page-kicker mb-2">Account</p>
          <h1 className="page-title text-2xl sm:text-3xl">Profile</h1>
        </div>
        <dl className="space-y-4">
          <div>
            <dt className="text-sm text-stone-500 dark:text-stone-400">Email</dt>
            <dd className="text-lg font-medium break-all">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-stone-500 dark:text-stone-400">
              Member since
            </dt>
            <dd className="text-lg font-medium">
              {formatMemberSince(user?.created_at)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-stone-500 dark:text-stone-400">Status</dt>
            <dd className="text-lg font-medium">
              {user?.is_active === false ? "Inactive" : "Active"}
            </dd>
          </div>
        </dl>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link to="/dashboard" className="w-full sm:w-auto">
            <Button variant="secondary" className="w-full sm:w-auto">
              Back to dashboard
            </Button>
          </Link>
          <Button variant="outline" onClick={logout} className="w-full sm:w-auto">
            Log out
          </Button>
        </div>
      </div>
    </div>
  );
}
