# spell-checker:ignore bcond pkgversion buildrequires autosetup PYTHONPATH noarch buildroot bindir sitelib numprocesses clib
%bcond_with     check
%bcond_with     privileged_tests
#global source_date_epoch_from_changelog 0
#global clamp_mtime_to_source_date_epoch 1

Name:           subprocess-tee
Version:        VERSION_PLACEHOLDER
Release:        1%{?dist}
Summary:        subprocess-tee

License:        MIT
URL:            https://github.com/pycontribs/subprocess-tee
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-build
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  python%{python3_pkgversion}-devel
%if %{with check}
# These are required for tests:
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  git-core
%endif


%description
subprocess-tee


%prep
%autosetup


%build
%pyproject_wheel


%generate_buildrequires
%pyproject_buildrequires


%install
%pyproject_install
%pyproject_save_files subprocess_tee

%check
%if %{with check}
  pytest \
  -v \
  --disable-pytest-warnings \
  --numprocesses=auto \
test
%endif


%files -f %{pyproject_files}
%license LICENSE
%doc README.md

%changelog
