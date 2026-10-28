<!-- Source: https://github.com/rclone/rclone/blob/master/backend/union/union.go (raw: https://raw.githubusercontent.com/rclone/rclone/master/backend/union/union.go)
     Fetched: 2026-10-28. Excerpt: NewFs (lines 896-975) and List (lines 684-713), verbatim. -->

```go
func (f *Fs) List(ctx context.Context, dir string) (entries fs.DirEntries, err error) {
	entriesList := make([][]upstream.Entry, len(f.upstreams))
	errs := Errors(make([]error, len(f.upstreams)))
	multithread(len(f.upstreams), func(i int) {
		u := f.upstreams[i]
		entries, err := u.List(ctx, dir)
		if err != nil {
			errs[i] = fmt.Errorf("%s: %w", u.Name(), err)
			return
		}
		uEntries := make([]upstream.Entry, len(entries))
		for j, e := range entries {
			uEntries[j], _ = u.WrapEntry(e)
		}
		entriesList[i] = uEntries
	})
	if len(errs) == len(errs.FilterNil()) {
		errs = errs.Map(func(e error) error {
			if errors.Is(e, fs.ErrorDirNotFound) {
				return nil
			}
			return e
		})
		if len(errs) == 0 {
			return nil, fs.ErrorDirNotFound
		}
		return nil, errs.Err()
	}
	return f.mergeDirEntries(entriesList)
}

// ...
func NewFs(ctx context.Context, name, root string, m configmap.Mapper) (fs.Fs, error) {
	// Parse config into Options struct
	opt := new(common.Options)
	err := configstruct.Set(m, opt)
	if err != nil {
		return nil, err
	}
	// Backward compatible to old config
	if len(opt.Upstreams) == 0 && len(opt.Remotes) > 0 {
		for i := range len(opt.Remotes) - 1 {
			opt.Remotes[i] += ":ro"
		}
		opt.Upstreams = opt.Remotes
	}
	if len(opt.Upstreams) == 0 {
		return nil, errors.New("union can't point to an empty upstream - check the value of the upstreams setting")
	}
	if len(opt.Upstreams) == 1 {
		return nil, errors.New("union can't point to a single upstream - check the value of the upstreams setting")
	}
	for _, u := range opt.Upstreams {
		if strings.HasPrefix(u, name+":") {
			return nil, errors.New("can't point union remote at itself - check the value of the upstreams setting")
		}
	}

	root = strings.Trim(root, "/")
	upstreams := make([]*upstream.Fs, len(opt.Upstreams))
	errs := Errors(make([]error, len(opt.Upstreams)))
	multithread(len(opt.Upstreams), func(i int) {
		u := opt.Upstreams[i]
		upstreams[i], errs[i] = upstream.New(ctx, u, root, opt)
	})
	var usedUpstreams []*upstream.Fs
	var fserr error
	for i, err := range errs {
		if err != nil && err != fs.ErrorIsFile {
			return nil, err
		}
		// Only the upstreams returns ErrorIsFile would be used if any
		if err == fs.ErrorIsFile {
			usedUpstreams = append(usedUpstreams, upstreams[i])
			fserr = fs.ErrorIsFile
		}
	}
	if fserr == nil {
		usedUpstreams = upstreams
	}

	f := &Fs{
		name:      name,
		root:      root,
		opt:       *opt,
		upstreams: usedUpstreams,
	}
	// Correct root if definitely pointing to a file
	if fserr == fs.ErrorIsFile {
		f.root = path.Dir(f.root)
		if f.root == "." || f.root == "/" {
			f.root = ""
		}
	}
	err = upstream.Prepare(f.upstreams)
	if err != nil {
		return nil, err
	}
	f.actionPolicy, err = policy.Get(opt.ActionPolicy)
	if err != nil {
		return nil, err
	}
	f.createPolicy, err = policy.Get(opt.CreatePolicy)
	if err != nil {
		return nil, err
	}
	f.searchPolicy, err = policy.Get(opt.SearchPolicy)
	if err != nil {
		return nil, err
	}
	fs.Debugf(f, "actionPolicy = %T, createPolicy = %T, searchPolicy = %T", f.actionPolicy, f.createPolicy, f.searchPolicy)
	var features = (&fs.Features{
```
